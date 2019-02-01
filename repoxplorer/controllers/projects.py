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

    @expose('json')
    def projects(self, pid=None):
        projects_index = Projects()
        if pid:
            project = projects_index.get(pid)
            if not project:
                abort(404, detail="Project ID has not been found")
            return {pid: projects_index.get(pid)}
        else:
            projects = projects_index.get_projects(
                source=['name', 'description', 'logo', 'refs'])
            _projects = OrderedDict(
                sorted(list(projects.items()), key=lambda t: t[0]))
            return {'projects': _projects,
                    'tags': projects_index.get_tags()}

    @expose('json')
    def repos(self, pid=None, tid=None):
        projects_index = Projects()
        if not pid and not tid:
            abort(404,
                  detail="A tag ID or project ID must be passed as parameter")
        if pid:
            project = projects_index.get(pid)
        else:
            if tid in projects_index.get_tags():
                refs = projects_index.get_references_from_tags(tid)
                project = {'refs': refs}
            else:
                project = None
        if not project:
            abort(404,
                  detail='Project ID or Tag ID has not been found')
        return project['refs']
