# Copyright 2016-2017, Fabien Boucher
# Copyright 2016-2017, Red Hat
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


from pecan import expose
from pecan import abort
from pecan import request

from repoxplorer.controllers import groups
from repoxplorer.controllers import users
from repoxplorer.controllers import histo
from repoxplorer.controllers import infos
from repoxplorer.controllers import tops
from repoxplorer.controllers import search
from repoxplorer.controllers import status
from repoxplorer.controllers import projects
from repoxplorer.controllers import metadata
from repoxplorer.controllers import tags
from repoxplorer.controllers import commits


class V1Controller(object):

    infos = infos.InfosController()
    groups = groups.GroupsController()
    users = users.UsersController()
    histo = histo.HistoController()
    tops = tops.TopsController()
    search = search.SearchController()
    status = status.StatusController()
    projects = projects.ProjectsController()
    metadata = metadata.MetadataController()
    tags = tags.TagsController()
    commits = commits.CommitsController()


class APIController(object):

    v1 = V1Controller()


class ErrorController(object):

    @expose('json')
    def e404(self):
        message = str(request.environ.get('pecan.original_exception', ''))
        return dict(status=404, message=message)


class RootController(object):

    api = APIController()
    error = ErrorController()

    @expose(template='index.html')
    def index(self):
        return {}

    @expose(template='groups.html')
    def groups(self):
        return {}

    @expose(template='projects.html')
    def projects(self):
        return {}

    @expose(template='contributors.html')
    def contributors(self):
        return {}

    @expose(template='contributor.html')
    def contributor(self, cid, pid=None,
                    dfrom=None, dto=None,
                    inc_merge_commit=None,
                    inc_repos_detail=None):

        if not cid:
            abort(404,
                  detail="A contributor ID is mandatory")

        return {}

    @expose(template='group.html')
    def group(self, gid, pid=None, dfrom=None, dto=None,
              inc_merge_commit=None,
              inc_repos_detail=None):

        if not gid:
            abort(404,
                  detail="A group ID is mandatory")

        return {}

    @expose(template='project.html')
    def project(self, pid=None, tid=None, dfrom=None, dto=None,
                inc_merge_commit=None, inc_repos=None, metadata=None,
                exc_groups=None):

        if not pid and not tid:
            abort(404,
                  detail="tag ID or project ID is mandatory")
        if pid and tid:
            abort(404,
                  detail="tag ID and project ID can't be requested together")

        return {}
