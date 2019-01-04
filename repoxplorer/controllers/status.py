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

import itertools

from pecan import expose

from pecan import conf
from repoxplorer import version
from repoxplorer.index.projects import Projects

rx_version = version.get_version()
index_custom_html = conf.get('index_custom_html', '')


class StatusController(object):

    @expose('json')
    def version(self):
        return {'version': rx_version}

    def get_status(self):
        projects_index = Projects()
        projects = projects_index.get_projects()
        num_projects = len(projects)
        num_repos = len(set([
            ref['name'] for
            ref in itertools.chain(
                *[p['refs'] for p in projects.values()])]))
        return {'customtext': index_custom_html,
                'projects': num_projects,
                'repos': num_repos,
                'users_endpoint': conf.get('users_endpoint', False),
                'version': rx_version}

    @expose('json')
    def status(self):
        return self.get_status()
