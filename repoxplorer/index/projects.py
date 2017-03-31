# Copyright 2016, Fabien Boucher
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.


import yaml
import copy
import time
import logging

from pecan import conf

from jsonschema import validate as schema_validate

from repoxplorer.index.yamlbackend import YAMLBackend

logger = logging.getLogger(__name__)


project_templates_schema = """
$schema: http://json-schema.org/draft-04/schema

definitions:
  release:
    type: object
    additionalProperties: false
    required:
    - name
    - date
    properties:
      name:
        type: string
      date:
        type: string

type: object
properties:
  project-templates:
    type: object
    additionalProperties: false
    patternProperties:
      ^[a-zA-Z0-9_-]+$:
        type: object
        additionalProperties: false
        required:
        - uri
        - branches
        properties:
          uri:
            type: string
          gitweb:
            type: string
          branches:
            type: array
            items:
              type: string
              minItems: 1
          tags:
            type: array
            items:
              type: string
          parsers:
            type: array
            items:
              type: string
          releases:
            type: array
            items:
              $ref: "#/definitions/release"
"""


project_templates_example = """
templates:
  default:
    uri: https://github.com/%(name)s
    branches:
    - master
    - stable/mitaka
    - stable/newton
    - stable/ocata
    gitweb: https://github.com/%(name)s/commit/%%(sha)s
    parsers:
    - .*(blueprint) ([^ .]+).*
    releases:
    - name: 1.0
      date: 12/20/2016
    - name: 2.0
      date: 12/31/2016
    tags:
    - openstack
    - language:python
    - type:cloud
"""

projects_schema = """
$schema: http://json-schema.org/draft-04/schema

type: object
properties:
  projects:
    type: object
    additionalProperties: false
    patternProperties:
      ^[a-zA-Z0-9_/-]+$:
        type: object
        additionalProperties: false
        patternProperties:
          ^[a-zA-Z0-9_/-]+$:
            type: object
            additionalProperties: false
            properties:
              template:
                type: string
"""

projects_example = """
projects:
  Barbican:
    openstack/barbican:
      template: default
    openstack/python-barbicanclient:
      template: default
  Swift:
    openstack/swift:
      template: default
    openstack/python-swiftclient:
      template: default
"""


class Projects(object):
    """ This class manages definition of projects
    """
    def __init__(self, db_path=None):
        if db_path:
            path = db_path
        else:
            path = conf.db_path
        self.projects = {}
        self.yback = YAMLBackend(
            path, db_default_file=conf.db_default_file)
        self.yback.load_db()
        self.default_data, self.data = self.yback.get_data()
        self._merge()
        self.enriched = False

    def _merge(self):
        """ Merge self.data and inherites from default_data
        """
        merged_templates = {}
        merged_projects = {}
        for d in self.data:
            templates = d.get('project-templates', {})
            projects = d.get('projects', {})
            merged_templates.update(copy.copy(templates))
            merged_projects.update(copy.copy(projects))

        self.templates = {}
        self.projects = {}
        if self.default_data:
            self.templates = copy.copy(
                self.default_data.get('project-templates', {}))
            self.projects = copy.copy(
                self.default_data.get('projects', {}))

        self.templates.update(merged_templates)
        self.projects.update(merged_projects)

    def _enrich_projects(self):
        self.gitweb_lookup = {}
        # First resolve templates references
        for pid, repos in self.projects.items():
            for rid, repo in repos.items():
                repo.update(copy.deepcopy(
                    self.templates[repo['template']]))
                del repo['template']
                for key in ('uri', 'gitweb'):
                    repo[key] = repo[key] % {'name': rid}
                if 'tags' not in repo:
                    repo['tags'] = []
                if 'parsers' not in repo:
                    repo['parsers'] = []
                if 'releases' not in repo:
                    repo['releases'] = []
                for release in repo['releases']:
                    epoch = time.mktime(
                        time.strptime(release['date'], "%m/%d/%Y"))
                    release['date'] = epoch
                if 'gitweb' in repo:
                    su = '%s:%s' % (repo['uri'], rid)
                    self.gitweb_lookup[su] = repo['gitweb']
        self.enriched = True

    def _check_basic(self, key, schema, identifier):
        """ Verify schema and no data duplicated
        """
        issues = []
        ids = set()
        for d in self.data:
            data = d.get(key, {})
            try:
                schema_validate({key: data},
                                yaml.load(schema))
            except Exception, e:
                issues.append(e.message)
            duplicated = set(data.keys()) & ids
            if duplicated:
                issues.append("%s IDs [%s,] are duplicated" % (
                              identifier, ",".join(duplicated)))
            ids.update(set(data.keys()))
        return ids, issues

    def _validate_templates(self):
        """ Validate self.data consistencies for templates
        """
        ids, issues = self._check_basic('project-templates',
                                        project_templates_schema,
                                        'Project template')
        if issues:
            return ids, issues
        # Check uncovered by the schema validator
        for d in self.data:
            templates = d.get('project-templates', {})
            for tid, templates in templates.items():
                if 'releases' in templates:
                    for r in templates['releases']:
                        try:
                            time.mktime(
                                time.strptime(r['date'], "%m/%d/%Y"))
                        except Exception:
                            issues.append("Wrong date format %s defined "
                                          "in template %s" % (r['date'], tid))
        return ids, issues

    def _validate_projects(self, tids):
        """ Validate self.data consistencies for projects
        """
        _, issues = self._check_basic('projects',
                                      projects_schema,
                                      'Project')
        if issues:
            return issues
        # Check template dependencies
        for d in self.data:
            projects = d.get('projects', {})
            for pid, project in projects.items():
                for rid, repo in project.items():
                    template = repo['template']
                    if template not in tids:
                        issues.append("Project ID '%s' Repo ID '%s' "
                                      "references an unknown template %s" % (
                                          pid, rid, template))
        return issues

    def validate(self):
        validation_issues = []
        tids, issues = self._validate_templates()
        validation_issues.extend(issues)
        issues = self._validate_projects(tids)
        validation_issues.extend(issues)
        return validation_issues

    def get_projects(self):
        if not self.enriched:
            self._enrich_projects()
        return self.projects
