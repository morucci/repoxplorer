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


import os
import copy
import logging
import cPickle

from datetime import datetime

from pecan import conf

from repoxplorer.index import YAMLDefinition
from repoxplorer.index import date2epoch


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
      ^[a-zA-Z0-9_/\. -]+$:
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
          paths:
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
          index-tags:
            type: boolean
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
      date: 2016-12-20
    - name: 2.0
      date: 2016-12-31
    tags:
    - openstack
    - language:python
    - type:cloud
    paths:
    - project/tests/
    index-tags: true
"""

projects_schema = """
$schema: http://json-schema.org/draft-04/schema

type: object
properties:
  projects:
    type: object
    additionalProperties: false
    patternProperties:
      ^[a-zA-Z0-9_/\. -]+$:
        type: object
        additionalProperties: false
        properties:
          description:
            type: string
          logo:
            type: string
          repos:
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
                  paths:
                    type: array
                    items:
                      type: string
                  tags:
                    type: array
                    items:
                      type: string
                  branches:
                    type: array
                    items:
                      type: string
                      minItems: 1
"""

projects_example = """
projects:
  Barbican:
    repos:
      openstack/barbican:
        template: default
      openstack/python-barbicanclient:
        template: default
        tags:
        - client
        - language:python
        paths:
        - project/tests/
  Swift:
    repos:
      openstack/swift:
        template: default
        branches:
        - dev
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
        self.flatten = {}
        self.ref2projects_lookup = {}
        db_path = db_path or conf.db_path
        self.cached_projects_enriched_path = os.path.join(
            db_path, 'projects-enriched.cache')
        self.cached_projects_flatten_path = os.path.join(
            db_path, 'projects-flatten.cache')

    def _merge(self):
        """ Merge self.data and inherites from default_data
        """
        # TODO(fbo): This could even be put in cache
        merged_templates = {}
        merged_projects = {}
        for d in self.data:
            templates = d.get('project-templates', {})
            projects = d.get('projects', {})
            merged_templates.update(copy.copy(templates))
            for p, v in projects.items():
                merged_projects.setdefault(p, copy.copy(v))
                merged_projects[p]['repos'].update(copy.copy(v['repos']))

        self.templates = {}
        self.projects = {}
        if self.default_data:
            self.templates = copy.copy(
                self.default_data.get('project-templates', {}))
            self.projects = copy.copy(
                self.default_data.get('projects', {}))

        self.templates.update(merged_templates)
        self.projects.update(merged_projects)

    def _save_to_cache(self, path, hash, data):
        ddata = (hash, data)
        if not os.path.isdir(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        cPickle.dump(ddata, open(path, 'w'), cPickle.HIGHEST_PROTOCOL)

    def _read_from_cache(self, path, hash):
        try:
            registered_hash, data = cPickle.load(open(path))
        except Exception as err:
            logger.debug('Unable to read cache %s: %s' % (path, err))
            return None
        if hash == registered_hash:
            return data
        return None

    def _enrich_projects(self):
        cached_data = self._read_from_cache(
            self.cached_projects_enriched_path, self.hashes_str)
        if cached_data is not None:
            self.projects = cached_data[0]
            self.gitweb_lookup = cached_data[1]
            self.enriched = True
            logger.debug('Read projects enriched from cache %s' % (
                self.cached_projects_enriched_path))
        if self.enriched:
            return
        # First resolve templates references
        for pid, detail in self.projects.items():
            for rid, repo in detail['repos'].items():
                # Save tags mentioned for a repo
                tags = []
                if 'tags' in repo and repo['tags']:
                    tags = copy.copy(repo['tags'])
                # Save branches mentioned for a repo
                branches = []
                if 'branches' in repo:
                    branches = copy.copy(repo['branches'])
                # Save paths mentioned for a repo
                paths = []
                if 'paths' in repo:
                    paths = copy.copy(repo['paths'])
                # Apply the template
                if 'template' in repo:
                    repo.update(copy.deepcopy(
                        self.templates[repo['template']]))
                    del repo['template']
                # Process uri and gitweb string
                for key in ('uri', 'gitweb'):
                    if key in repo:
                        repo[key] = repo[key] % {'name': rid}
                # Re-apply saved tags
                if 'tags' not in repo:
                    repo['tags'] = []
                repo['tags'].extend(tags)
                repo['tags'] = list(set(repo['tags']))
                # Restore defined branches at repo level
                if branches:
                    repo['branches'] = branches
                # Restore defined paths at repo level
                if paths:
                    repo['paths'] = paths
                # Apply default values
                if 'parsers' not in repo:
                    repo['parsers'] = []
                if 'releases' not in repo:
                    repo['releases'] = []
                if 'index-tags' not in repo:
                    repo['index-tags'] = True
                # Transform date to epoch
                for release in repo['releases']:
                    release['date'] = date2epoch(release['date'])
                # Fill the lookup table for gitweb links
                if 'gitweb' in repo:
                    su = '%s:%s' % (repo['uri'], rid)
                    self.gitweb_lookup[su] = repo['gitweb']
        data = (self.projects, self.gitweb_lookup)
        self._save_to_cache(
            self.cached_projects_enriched_path, self.hashes_str, data)
        logger.debug('Saved projects enriched cache in %s' % (
            self.cached_projects_enriched_path))
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
                            datetime.strptime(r['date'], "%Y-%m-%d")
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
            for pid, detail in projects.items():
                for rid, repo in detail['repos'].items():
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
        if self.flatten:
            return self.flatten
        cached_data = self._read_from_cache(
            self.cached_projects_flatten_path, self.hashes_str)
        if cached_data is not None:
            self.flatten = cached_data
            logger.debug('Read projects flatten from cache %s' % (
                self.cached_projects_flatten_path))
            return self.flatten
        if not self.enriched:
            self._enrich_projects()
        # This transforms repos into refs by listing
        # their branches. A project is now
        # a list of refs
        for pid, detail in self.projects.items():
            self.flatten[pid] = {
                'repos': [],
                'description': detail.get('description'),
                'logo': detail.get('logo')
            }
            for rid, repo in detail['repos'].items():
                for branch in repo['branches']:
                    r = {}
                    r.update(copy.deepcopy(repo))
                    r['name'] = rid
                    r['branch'] = branch
                    del r['branches']
                    self.flatten[pid]['repos'].append(r)
        self._save_to_cache(
            self.cached_projects_flatten_path, self.hashes_str, self.flatten)
        logger.debug('Saved projects flatten cache in %s' % (
            self.cached_projects_flatten_path))
        return self.flatten

    def get_tags(self):
        projects = self.get_projects()
        tags = {}
        for _, details in projects.items():
            for ref in details['repos']:
                for tag in ref.get('tags', []):
                    tags.setdefault(tag, {'repos': []})
                    tags[tag]['repos'].append(ref)
        return tags

    def get_ref2projects_lookup(self):
        if self.ref2projects_lookup:
            return self.ref2projects_lookup
        projects = self.get_projects()
        # Fill ref2project lookup
        for pname, details in projects.items():
            for r in details['repos']:
                full_rid = "%s:%s:%s" % (r['uri'],
                                         r['name'],
                                         r['branch'])
                self.ref2projects_lookup.setdefault(
                    full_rid, set()).update([pname])
        return self.ref2projects_lookup

    def get_gitweb_link(self, simple_uri):
        return self.gitweb_lookup.get(simple_uri, "")
