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
