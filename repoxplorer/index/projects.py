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

logger = logging.getLogger(__name__)


class NoTemplateFound(Exception):
    pass


class Projects(object):
    def __init__(self, projects_file_path=None):
        if projects_file_path:
            path = projects_file_path
        else:
            path = conf.projects_file_path
        try:
            self.data = yaml.load(file(path))
        except Exception, e:
            logger.error(
                'Unable to read projects.yaml (%s). Default is empty.' % e)
            self.data = []
        self.projects = {}
        self.gitweb_lookup = {}
        self.projects_raw = {}
        self.templates_raw = {}
        self.tags = {}
        if self.data:
            self.projects_raw = self.data['projects']
            self.templates_raw = self.data['templates']
        for pid, details in self.projects_raw.items():
            self.projects[pid] = []
            for repo in details:
                if 'template' in repo:
                    try:
                        tmpl = self.find_template_by_name(repo['template'])
                    except NoTemplateFound:
                        logger.error(
                            "%s requests a non exisiting template %s" % (
                                repo['name'], repo['template']))
                        continue
                    del repo['template']
                    for k in repo.keys():
                        # Remove already existing key from the template
                        # to prevent deletion of special configuration
                        if k in tmpl.keys():
                            del tmpl[k]
                    repo.update(tmpl)
                    repo_computed = {}
                    for k, v in repo.items():
                        if isinstance(v, str):
                            repo_computed[k] = v % repo
                        else:
                            repo_computed[k] = v
                    repo = repo_computed
                self.projects[pid].append(repo)
                if 'releases' in repo:
                    try:
                        assert isinstance(repo['releases'], list)
                        rels = []
                        for release in repo['releases']:
                            assert isinstance(release, dict)
                            assert len(release) == 2
                            assert 'name' in release
                            assert 'date' in release
                            epoch = time.mktime(
                                time.strptime(release['date'], "%d/%m/%Y"))
                            rels.append({'name': release['name'],
                                         'date': epoch,
                                         'project': pid})
                    except Exception, e:
                        logger.error(
                            "%s unable to parse releases dates (%s)" % (
                                repo['name'], e))
                    repo['releases'] = rels
                if 'gitweb' in repo:
                    simple_uri = '%s:%s' % (repo['uri'], repo['name'])
                    self.gitweb_lookup[simple_uri] = repo['gitweb']
                if 'tags' in repo:
                    assert isinstance(repo['tags'], list)
                    for tag in repo['tags']:
                        self.tags.setdefault(tag, [])
                        self.tags[tag].append(repo)
                else:
                    repo['tags'] = []
                if 'parsers' not in repo:
                    repo['parsers'] = []

    def get_repo_id(self, repo):
        return "%s:%s:%s" % (
            repo['uri'], repo['name'], repo['branch'])

    def find_template_by_name(self, name):
        try:
            tmpl = [t for t in self.templates_raw
                    if t['name'] == name][0]
        except KeyError:
            raise NoTemplateFound
        ret = copy.deepcopy(tmpl)
        del ret['name']
        return ret

    def get_projects(self):
        return self.projects

    def get_gitweb_link(self, simple_uri):
        return self.gitweb_lookup.get(simple_uri, "")

    def get_repos_by_tag(self, tag):
        return self.tags.get(tag, [])
