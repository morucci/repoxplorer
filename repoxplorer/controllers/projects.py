# Copyright 2017, Fabien Boucher
# Copyright 2017, Red Hat
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

from collections import OrderedDict

from pecan import expose

from pecan import conf
from repoxplorer import version
from repoxplorer.index.projects import Projects

indexname = 'repoxplorer'
rx_version = version.get_version()
index_custom_html = conf.get('index_custom_html', '')


class ProjectsController(object):

    def get_projects(self):
        projects_index = Projects()
        projects = projects_index.get_projects()
        projects = OrderedDict(
            sorted(projects.items(), key=lambda t: t[0]))
        tags = projects_index.get_tags()
        return {'projects': projects,
                'tags': tags.keys()}

    @expose('json')
    def projects(self):
        return self.get_projects()
