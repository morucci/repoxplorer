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
import logging

from pecan import conf

logger = logging.getLogger(__name__)


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
            self.data = {}
        self.projects = {}
        self.gitweb_lookup = {}
        for elm in self.data:
            pid = elm.keys()[0]
            self.projects[pid] = []
            for prj in elm[pid]:
                self.projects[pid].append(prj)
                if 'gitweb' in prj:
                    simple_uri = '%s:%s' % (prj['uri'], prj['name'])
                    self.gitweb_lookup[simple_uri] = prj['gitweb']

    def get_projects(self):
        return self.projects

    def get_gitweb_link(self, simple_uri):
        return self.gitweb_lookup.get(simple_uri, "")
