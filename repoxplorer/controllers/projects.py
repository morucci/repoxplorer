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

from pecan import abort
from pecan import expose

from repoxplorer import version
from repoxplorer.index.projects import Projects

rx_version = version.get_version()


class ProjectsController(object):

    def get_repos(self, pid=None, tid=None):
        projects_index = Projects()
        if pid:
            repos = projects_index.get_projects().get(pid)
        elif tid:
            repos = projects_index.get_tags().get(tid)
        else:
            abort(404,
                  detail="A tag ID or project ID must be passed as parameter")

        if repos is None:
            abort(404,
                  detail='Project ID or Tag ID has not been found')
        return repos

    def get_projects(self, pid=None):
        projects_index = Projects()
        projects = projects_index.get_projects()
        if pid:
            if pid not in projects:
                abort(404, detail="Project ID has not been found")
            return {pid: projects.get(pid)}
        else:
            projects = OrderedDict(
                sorted(projects.items(), key=lambda t: t[0]))
            tags = projects_index.get_tags()
            return {'projects': projects,
                    'tags': tags.keys()}

    @expose('json')
    def projects(self, pid=None):
        return self.get_projects(pid)

    @expose('json')
    def repos(self, pid=None, tid=None):
        return self.get_repos(pid, tid)['repos']
