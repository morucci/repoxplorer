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
from pecan import conf
from pecan import request

from repoxplorer.controllers import utils
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

from repoxplorer import index
from repoxplorer import version
from repoxplorer.index.commits import Commits
from repoxplorer.index.contributors import Contributors


indexname = 'repoxplorer'
xorkey = conf.get('xorkey') or 'default'
rx_version = version.get_version()


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

# The use of templates for some pages will be replaced soon
# Pages will be rederred by JS only. Today rendering
# is a mixed of Mako templating and JS

    @expose(template='index.html')
    def index(self):
        return self.api.v1.status.get_status()

    @expose(template='groups.html')
    def groups(self):
        return {'version': rx_version}

    @expose(template='projects.html')
    def projects(self):
        return {'version': rx_version}

    @expose(template='contributors.html')
    def contributors(self):
        return {'version': rx_version}

    @expose(template='contributor.html')
    def contributor(self, cid, pid=None,
                    dfrom=None, dto=None,
                    inc_merge_commit=None,
                    inc_repos_detail=None):

        if not cid:
            abort(404,
                  detail="A contributor ID is mandatory")

        ocid = cid
        try:
            cid = utils.decrypt(xorkey, cid)
        except Exception:
            # Unable to uncypher the cid return and let
            # the JS handle a comprehensible display
            return {
                'name': 'Unknown contributor',
                'cid': ocid,
                'version': rx_version}

        # TODO: remove the name in the mako template then remove that below
        c = Commits(index.Connector(index=indexname))
        idents = Contributors()
        iid, ident = idents.get_ident_by_id(cid)
        if not ident:
            # No ident has been declared for that contributor
            iid, ident = idents.get_ident_by_email(cid)
        name = ident['name']
        if not name:
            raw_names = c.get_commits_author_name_by_emails([cid])
            if cid not in raw_names:
                name = 'Unknown contributor'
            else:
                name = raw_names[cid]

        return {
            'name': name,
            'cid': ocid,
            'version': rx_version}

    @expose(template='group.html')
    def group(self, gid, pid=None, dfrom=None, dto=None,
              inc_merge_commit=None,
              inc_repos_detail=None):

        if not gid:
            abort(404,
                  detail="A group ID is mandatory")

        return {'gid': gid,
                'version': rx_version}

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

        return {'pid': pid,
                'tid': tid,
                'version': rx_version}
