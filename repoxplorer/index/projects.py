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

from datetime import datetime

from elasticsearch.helpers import bulk
from elasticsearch.helpers import BulkIndexError
from elasticsearch.helpers import scan as scanner

from pecan import conf

from repoxplorer import index
from repoxplorer.index import YAMLDefinition
from repoxplorer.index import add_params
from repoxplorer.index import date2epoch

logger = logging.getLogger(__name__)


project_templates_schema = r"""
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
      ^[a-zA-Z0-9_/\. \-\+]+$:
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

projects_schema = r"""
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
  projects:
    type: object
    additionalProperties: false
    patternProperties:
      ^[a-zA-Z0-9_/\. \-\+]+$:
        type: object
        additionalProperties: false
        properties:
          description:
            type: string
          logo:
            type: string
          meta-ref:
            type: boolean
          bots-group:
            type: string
          releases:
            type: array
            items:
              $ref: "#/definitions/release"
          repos:
            type: object
            additionalProperties: false
            patternProperties:
              ^[a-zA-Z0-9_/\. \-\+]+$:
                type: object
                additionalProperties: false
                required:
                - template
                properties:
                  template:
                    type: string
                  description:
                    type: string
                  paths:
                    type: array
                    items:
                      type: string
                  tags:
                    type: array
                    items:
                      type: string
                  forks:
                    type: integer
                  stars:
                    type: integer
                  watchers:
                    type: integer
                  branches:
                    type: array
                    items:
                      type: string
                      minItems: 1
"""

projects_example = """
projects:
  Barbican:
    description: The Barbican project
    bots-group: openstack-ci-bots
    releases:
    - name: ocata
      date: 2017-02-22
    repos:
      openstack/barbican:
        template: default
      openstack/python-barbicanclient:
        template: default
        description: The barbican client
        forks: 10
        watchers: 20
        stars: 30
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


class EProjects(object):

    PROPERTIES = {
        "aname": {"type": "text"},
        "name": {"type": "keyword"},
        "description": {"type": "text"},
        "logo": {"type": "binary"},
        "meta-ref": {"type": "boolean"},
        "bots-group": {"type": "keyword"},
        "index-tags": {"type": "boolean"},
        "project": {"type": "keyword"},
        "releases": {
            "type": "nested",
            "properties": {
                "name": {"type": "keyword"},
                "date": {"type": "keyword"},
            }
        },
        "refs": {
            "type": "nested",
            "properties": {
                "aname": {"type": "text"},
                "name": {"type": "keyword"},
                "description": {"type": "text"},
                "forks": {"type": "integer"},
                "watchers": {"type": "integer"},
                "stars": {"type": "integer"},
                "uri": {"type": "keyword"},
                "gitweb": {"type": "keyword"},
                "branch": {"type": "keyword"},
                "tags": {"type": "keyword"},
                "fullrid": {"type": "keyword"},
                "shortrid": {"type": "keyword"},
                "paths": {"type": "keyword"},
                "parsers": {"type": "keyword"},
                "index-tags": {"type": "boolean"},
                "releases": {
                    "type": "nested",
                    "properties": {
                        "name": {"type": "keyword"},
                        "date": {"type": "keyword"},
                        }
                    }
                }
            }
        }

    def __init__(self, connector=None):
        self.es = connector.es
        self.ic = connector.ic
        self.index = connector.index
        self.dbname = 'projects'
        self.mapping = {
            self.dbname: {
                "properties": self.PROPERTIES,
            }
        }

        if not self.ic.exists_type(index=self.index,
                                   doc_type=self.dbname):
            kwargs = add_params(self.es)
            self.ic.put_mapping(
                index=self.index, doc_type=self.dbname, body=self.mapping,
                **kwargs)

    def manage_bulk_err(self, exc):
        errs = [e['create']['error'] for e in exc[1]]
        if not all([True for e in errs if
                    e['type'] == 'document_already_exists_exception']):
            raise Exception(
                "Unable to create one or more doc: %s" % errs)

    def create(self, docs):
        def gen():
            for pid, doc in docs:
                d = {}
                d['_index'] = self.index
                d['_type'] = self.dbname
                d['_op_type'] = 'create'
                d['_id'] = pid
                d['_source'] = doc
                yield d
        try:
            bulk(self.es, gen())
        except BulkIndexError as exc:
            self.manage_bulk_err(exc)
        self.es.indices.refresh(index=self.index)

    def delete_all(self):
        def gen(docs):
            for doc in docs:
                d = {}
                d['_index'] = self.index
                d['_type'] = self.dbname
                d['_op_type'] = 'delete'
                d['_id'] = doc['_id']
                yield d
        bulk(self.es,
             gen(self.get_all(source=False)))
        self.es.indices.refresh(index=self.index)

    def load(self, projects, rid2projects):
        self.delete_all()
        self.create(projects.items())
        self.create(rid2projects.items())

    def get_all(self, source=True, type=None):
        query = {
            '_source': source,
            'query': {
                'match_all': {}
            }
        }
        return scanner(self.es, query=query, index=self.index)

    def get_by_id(self, id, source=True):
        try:
            res = self.es.get(index=self.index,
                              doc_type=self.dbname,
                              _source=source,
                              id=id)
            return res['_source']
        except Exception as e:
            logger.error('Unable to get the doc. %s' % e)

    def exists(self, id):
        return self.es.exists(
            index=self.index, doc_type=self.dbname, id=id)

    def get_by_attr_match(self, attribute, value, source=True):
        params = {'index': self.index}

        body = {
            "query": {
                'bool': {
                    'must': {'term': {attribute: value}},
                }
            }
        }
        params['body'] = body
        params['_source'] = source
        # TODO(fbo): Improve by doing it by bulk instead
        params['size'] = 10000
        res = self.es.search(**params)
        took = res['took']
        hits = res['hits']['total']
        docs = [r['_source'] for r in res['hits']['hits']]
        return took, hits, docs

    def get_by_nested_attr_match(
            self, attribute, values, source=True,
            inner_source=True, inner_hits_max=100):
        if not isinstance(values, list):
            values = (values,)
        params = {'index': self.index}
        body = {
            "query": {
                "bool": {
                    "must": {
                        "nested": {
                            "path": "refs",
                            "inner_hits": {
                                "_source": inner_source,
                                "size": inner_hits_max,
                            },
                            "query": {
                                "bool": {
                                    "should": [
                                        {"term":
                                            {"refs.%s" % attribute: value}}
                                        for value in values
                                    ]
                                }
                            }
                        }
                    }
                }
            }
        }
        params['body'] = body
        params['_source'] = source
        # TODO(fbo): Improve by doing it by bulk instead
        params['size'] = 10000
        res = self.es.search(**params)
        inner_hits = [r['inner_hits'] for r in res['hits']['hits']]
        took = res['took']
        hits = res['hits']['total']
        docs = [r['_source'] for r in res['hits']['hits']]
        return took, hits, docs, inner_hits

    def get_projects_by_fullrids(self, fullrids):
        body = {"ids": fullrids}
        try:
            res = self.es.mget(index=self.index,
                               doc_type=self.dbname,
                               _source=True,
                               body=body)
            return res['docs']
        except Exception as e:
            logger.error('Unable to get projects by fullrids. %s' % e)


class Projects(YAMLDefinition):
    """ This class manages definition of projects
    """
    def __init__(self, db_path=None, db_default_file=None, db_cache_path=None,
                 con=None, dump_yaml_in_index=None, vonly=False):
        self.db_path = db_path or conf.get('db_path')
        self.db_default_file = db_default_file or conf.get('db_default_file')
        self.db_cache_path = db_cache_path or conf.get('db_cache_path')
        if vonly:
            return
        # Use a separate index for projects (same as for users) as mapping
        # name/type collision will occured as commits have dynamic mapping
        self.eprojects = EProjects(
            connector=(con or index.Connector(index_suffix='projects')))
        self.el_version = self.eprojects.es.info().get(
            'version', {}).get('number', '')
        if dump_yaml_in_index:
            YAMLDefinition.__init__(
                self, self.db_path, self.db_default_file, self.db_cache_path)
            issues = self.validate()
            if issues:
                raise RuntimeError(issues)
            self._enrich_projects()
            projects, rid2projects = self._flatten_projects()
            self.eprojects.load(projects, rid2projects)

    def _merge(self):
        """ Merge self.data and inherites from default_data
        """
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

    def _enrich_projects(self):
        for detail in list(self.projects.values()):
            if 'meta-ref' not in detail:
                detail['meta-ref'] = False
            for rid, repo in list(detail['repos'].items()):
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

    def _flatten_projects(self):
        flatten = {}
        rid2projects = {}
        for pid, detail in self.projects.items():
            flatten[pid] = {
                'name': pid,
                'aname': pid,
                'meta-ref': detail.get('meta-ref'),
                'refs': [],
                'description': detail.get('description'),
                'logo': detail.get('logo'),
                'bots-group': detail.get('bots-group'),
                'releases': detail.get('releases', []),
            }
            for release in flatten[pid]['releases']:
                release['date'] = date2epoch(release['date'])
            for rid, repo in detail['repos'].items():
                for branch in repo['branches']:
                    r = {}
                    r.update(copy.deepcopy(repo))
                    r['name'] = rid
                    r['aname'] = rid
                    r['branch'] = branch
                    del r['branches']
                    r['fullrid'] = "%s:%s:%s" % (
                        r['uri'], r['name'], r['branch'])
                    r['shortrid'] = "%s:%s" % (r['uri'], r['name'])
                    flatten[pid]['refs'].append(r)
                    rid2projects.setdefault(r['fullrid'], {'project': []})
                    if pid not in rid2projects[r['fullrid']]['project']:
                        rid2projects[r['fullrid']]['project'].append(pid)
        return flatten, rid2projects

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
        if not hasattr(self, 'data'):
            YAMLDefinition.__init__(
                self, self.db_path, self.db_default_file, self.db_cache_path)
        validation_issues = []
        tids, issues = self._validate_templates()
        validation_issues.extend(issues)
        issues = self._validate_projects(tids)
        validation_issues.extend(issues)
        return validation_issues

    def get_projects(self, source=True):
        if isinstance(source, list) and 'name' not in source:
            source.append('name')
        projects = {}
        for project in list(self.eprojects.get_all(source)):
            if 'name' not in list(project['_source'].keys()):
                # We skip rid2projects objects as they have
                # only a 'project' key
                continue
            projects[project['_source']['name']] = project['_source']
        return projects

    def get(self, pid, source=True):
        return self.eprojects.get_by_id(pid, source)

    def exists(self, pid):
        return self.eprojects.exists(pid)

    def get_tags(self):
        projects = self.get_projects(source=['refs'])
        tags = set()
        for project in projects.values():
            for ref in project['refs']:
                for tag in ref.get('tags', []):
                    tags.add(tag)
        return list(tags)

    def get_gitweb_link(self, fullrid):
        source = 'name'
        inner_source = 'refs.gitweb'
        ret = self.eprojects.get_by_nested_attr_match(
            'fullrid', fullrid, source, inner_source, 1)
        # Get the first inner hit / let's see later if that cause limitations
        if not ret[3]:
            return ''
        ref = ret[3][0]['refs']['hits']['hits'][0]['_source']
        if self.el_version.find('5.') == 0:
            return ref.get('refs', {}).get('gitweb', '')
        else:
            return ref.get('gitweb', '')

    def get_projects_from_references(self, fullrids):
        if not fullrids:
            return []
        projects = set()
        ret = self.eprojects.get_projects_by_fullrids(fullrids)
        for _projects in [
                d.get('_source', {}).get('project', []) for d in ret]:
            for project in _projects:
                projects.add(project)
        return list(projects)

    def get_references_from_tags(self, tags):
        source = 'name'
        inner_source = [
            'refs.fullrid', 'refs.paths', 'refs.name', 'refs.branch']
        ret = self.eprojects.get_by_nested_attr_match(
            'tags', tags, source, inner_source)
        refs = []
        for hit in ret[3]:
            if self.el_version.find('5.') == 0:
                refs.extend([r['_source']['refs'] for r
                             in hit['refs']['hits']['hits']])
            else:
                refs.extend([r['_source'] for r
                             in hit['refs']['hits']['hits']])
        return refs
