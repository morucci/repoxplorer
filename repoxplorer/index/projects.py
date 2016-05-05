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


class Projects(object):
    def __init__(self, path="/usr/local/etc/projects.yaml"):
        self.data = yaml.load(file(path))
        self.projects = {}
        for elm in self.data:
            pid = elm.keys()[0]
            self.projects[pid] = []
            for prj in elm[pid]:
                self.projects[pid].append(prj)

    def get_projects(self):
        return self.projects
