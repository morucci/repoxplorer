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


import copy
import logging


from repoxplorer.index import YAMLDefinition
from repoxplorer.index import date2epoch
from datetime import datetime


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
      ^[a-zA-Z0-9_/\.-]+$:
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
      ^[a-zA-Z0-9_/\.-]+$:
        type: object
        additionalProperties: false
        patternProperties:
          ^[a-zA-Z0-9_/\.-]+$:
            type: object
            additionalProperties: false
            required:
            - template
            properties:
              template:
                type: string
              tags:
                type: array
                items:
                  type: string
"""

projects_example = """
projects:
  Barbican:
    openstack/barbican:
      template: default
    openstack/python-barbicanclient:
      template: default
      tags:
      - client
      - language:python
  Swift:
    openstack/swift:
      template: default
    openstack/python-swiftclient:
      template: default
"""


class Projects(YAMLDefinition):
    """ This class manages definition of projects
    """
    def __init__(self, db_path=None, db_default_file=None):
        YAMLDefinition.__init__(self, db_path, db_default_file)
        self.enriched = False
        self.gitweb_lookup = {}

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
        # First resolve templates references
        for pid, repos in self.projects.items():
            for rid, repo in repos.items():
                # Save tags mentioned for a repo
                tags = []
                if 'tags' in repo and repo['tags']:
                    tags = copy.copy(repo['tags'])
                # Apply the template
                repo.update(copy.deepcopy(
                    self.templates[repo['template']]))
                del repo['template']
                # Process uri and gitweb string
                for key in ('uri', 'gitweb'):
                    repo[key] = repo[key] % {'name': rid}
                # Re-apply saved tags
                if 'tags' not in repo:
                    repo['tags'] = []
                repo['tags'].extend(tags)
                # Apply default values
                if 'parsers' not in repo:
                    repo['parsers'] = []
                if 'releases' not in repo:
                    repo['releases'] = []
                # Transform date to epoch
                for release in repo['releases']:
                    release['date'] = date2epoch(release['date'])
                # Init a lookup table for gitweb links
                if 'gitweb' in repo:
                    su = '%s:%s' % (repo['uri'], rid)
                    self.gitweb_lookup[su] = repo['gitweb']
        self.enriched = True

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
                            datetime.strptime(r['date'], "%m/%d/%Y")
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

    def get_projects_raw(self):
        if not self.enriched:
            self._enrich_projects()
        return self.projects

    def get_projects(self):
        if not self.enriched:
            self._enrich_projects()
        flatten = {}
        # This transforms repos into refs by listing
        # their branches. A project is now
        # a list of refs
        for pid, repos in self.projects.items():
            flatten[pid] = []
            for rid, repo in repos.items():
                for branch in repo['branches']:
                    r = {}
                    r.update(copy.deepcopy(repo))
                    r['name'] = rid
                    r['branch'] = branch
                    del r['branches']
                    flatten[pid].append(r)
        return flatten

    def get_tags(self):
        projects = self.get_projects()
        tags = {}
        for _, refs in projects.items():
            for ref in refs:
                for tag in ref.get('tags', []):
                    tags.setdefault(tag, []).append(ref)
        return tags

    def get_gitweb_link(self, simple_uri):
        return self.gitweb_lookup.get(simple_uri, "")
