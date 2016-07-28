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
            logger.info(
                'Unable to read projects.yaml (%s). Default is empty.' % e)
            self.data = []
        self.projects = {}
        self.gitweb_lookup = {}
        self.projects_raw = []
        self.templates_raw = []
        if self.data:
            self._projects_raw = [d['projects'] for d in self.data
                                  if 'projects' in d]
            for project in self._projects_raw:
                self.projects_raw.extend(project)
            self._templates_raw = [d['templates'] for d in self.data
                                   if 'templates' in d]
            for template in self._templates_raw:
                self.templates_raw.extend(template)
        for elm in self.projects_raw:
            pid = elm.keys()[0]
            self.projects[pid] = []
            for prj in elm[pid]:
                if 'template' in prj:
                    try:
                        tmpl = self.find_template_by_name(prj['template'])
                    except NoTemplateFound:
                        logger.info(
                            "%s requests a non exisiting template %s" % (
                                prj['name'], prj['template']))
                        continue
                    del prj['template']
                    for k in prj.keys():
                        # Remove already existing key from the template
                        # to prevent deletion of special configuration
                        if k in tmpl.keys():
                            del tmpl[k]
                    prj.update(tmpl)
                    prj_computed = {}
                    for k, v in prj.items():
                        prj_computed[k] = v % prj
                    prj = prj_computed
                self.projects[pid].append(prj)
                if 'gitweb' in prj:
                    simple_uri = '%s:%s' % (prj['uri'], prj['name'])
                    self.gitweb_lookup[simple_uri] = prj['gitweb']

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
