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

from datetime import datetime

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
from repoxplorer.index.projects import Projects
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


class RootController(object):

    api = APIController()

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
        cid = utils.decrypt(xorkey, cid)
        if inc_merge_commit != 'on':
            include_merge_commit = False
        else:
            # The None value will return all whatever
            # the commit is a merge one or not
            include_merge_commit = None
        if dfrom:
            dfrom = datetime.strptime(
                dfrom, "%Y-%m-%d").strftime('%s')
        if dto:
            dto = datetime.strptime(
                dto, "%Y-%m-%d").strftime('%s')
        c = Commits(index.Connector(index=indexname))
        idents = Contributors()
        projects = Projects()
        iid, ident = idents.get_ident_by_id(cid)
        if not ident:
            # No ident has been declared for that contributor
            iid, ident = idents.get_ident_by_email(cid)
        mails = ident['emails']
        name = ident['name']
        if not name:
            if not name:
                raw_names = c.get_commits_author_name_by_emails([cid])
                if cid not in raw_names:
                    # TODO: get_commits_author_name_by_emails must
                    # support look by committer email too
                    name = 'Unamed'
                else:
                    name = raw_names[cid]

            name = raw_names[cid]

        p_filter = {}
        if pid:
            repos = projects.get_projects()[pid]
            p_filter = utils.get_references_filter(repos)

        query_kwargs = {
            'fromdate': dfrom,
            'todate': dto,
            'mails': mails,
            'merge_commit': include_merge_commit,
            'repos': p_filter,
        }

        if dfrom is None or dto is None:
            period = (None, None)
        else:
            period = (datetime.fromtimestamp(float(dfrom)),
                      datetime.fromtimestamp(float(dto)))

        top_projects = self.api.v1.tops.top_projects_sanitize(
            c, projects, query_kwargs, inc_repos_detail)

        return {'name': name,
                'period': period,
                'repos': top_projects[0],
                'repos_line_mdfds': top_projects[1],
                'cid': utils.encrypt(xorkey, cid),
                'empty': False,
                'inc_repos_detail': inc_repos_detail,
                'version': rx_version}

    @expose(template='group.html')
    def group(self, gid, pid=None, dfrom=None, dto=None,
              inc_merge_commit=None,
              inc_repos_detail=None):
        if inc_merge_commit != 'on':
            include_merge_commit = False
        else:
            # The None value will return all whatever
            # the commit is a merge one or not
            include_merge_commit = None
        if dfrom:
            dfrom = datetime.strptime(
                dfrom, "%Y-%m-%d").strftime('%s')
        if dto:
            dto = datetime.strptime(
                dto, "%Y-%m-%d").strftime('%s')
        c = Commits(index.Connector(index=indexname))
        idents = Contributors()
        projects = Projects()
        gid, group = idents.get_group_by_id(gid)
        if not group:
            abort(404,
                  detail="The group has not been found")
        mails = group['emails']
        domains = group.get('domains', [])
        members = {}
        for email in mails:
            iid, ident = idents.get_ident_by_email(email)
            members[iid] = ident

        p_filter = {}
        if pid:
            projects_index = Projects()
            repos = projects_index.get_projects()[pid]
            p_filter = utils.get_references_filter(repos)

        query_kwargs = {
            'fromdate': dfrom,
            'todate': dto,
            'mails': mails,
            'domains': domains,
            'merge_commit': include_merge_commit,
            'repos': p_filter,
        }

        top_projects = self.api.v1.tops.top_projects_sanitize(
            c, projects, query_kwargs, inc_repos_detail, pid)

        top_authors = self.api.v1.tops.authors.gbycommits(
            c, idents, query_kwargs)
        top_authors_modified = self.api.v1.tops.authors.gbylchanged(
            c, idents, query_kwargs)

        return {'name': gid,
                'top_authors': top_authors,
                'top_authors_modified': top_authors_modified,
                'repos': top_projects[0],
                'repos_line_mdfds': top_projects[1],
                'projects_amount': len(top_projects[2]),
                'repos_amount': len(top_projects[3]),
                'inc_repos_detail': inc_repos_detail,
                'gid': gid,
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

        if inc_merge_commit != 'on':
            include_merge_commit = False
        else:
            # The None value will return all whatever
            # the commit is a merge one or not
            include_merge_commit = None

        if dfrom:
            dfrom = datetime.strptime(dfrom, "%Y-%m-%d").strftime('%s')
        if dto:
            dto = datetime.strptime(dto, "%Y-%m-%d").strftime('%s')
        _metadata = []

        if metadata:
            metadata_splitted = metadata.split(',')
            for meta in metadata_splitted:
                try:
                    key, value = meta.split(':')
                    if value == '*':
                        value = None
                except ValueError:
                    continue
                _metadata.append((key, value))
        metadata = _metadata

        mails_to_exclude = {}
        domains_to_exclude = []
        if exc_groups:
            groups_splitted = exc_groups.split(',')
            idents = Contributors()
            for gid in groups_splitted:
                _, group = idents.get_group_by_id(gid)
                mails_to_exclude.update(group['emails'])
                domains_to_exclude.extend(group.get('domains', []))

        projects_index = Projects()
        if pid:
            repos = projects_index.get_projects().get(pid)
        else:
            repos = projects_index.get_tags().get(tid)

        if repos is None:
            abort(404,
                  detail='Project or Tag ID has not been found')

        p_filter = utils.get_references_filter(repos, inc_repos)

        query_kwargs = {
            'repos': p_filter,
            'fromdate': dfrom,
            'mails': mails_to_exclude,
            'domains': domains_to_exclude,
            'mails_neg': True,
            'todate': dto,
            'merge_commit': include_merge_commit,
            'metadata': metadata,
        }

        if dfrom is None or dto is None:
            period = (None, None)
        else:
            period = (datetime.fromtimestamp(float(dfrom)),
                      datetime.fromtimestamp(float(dto)))

        idents = Contributors()
        c = Commits(index.Connector(index=indexname))

        top_authors = self.api.v1.tops.authors.gbycommits(
            c, idents, query_kwargs)
        top_authors_modified = self.api.v1.tops.authors.gbylchanged(
            c, idents, query_kwargs)

        return {'pid': pid,
                'tid': tid,
                'top_authors': top_authors,
                'top_authors_modified': top_authors_modified,
                'repos': repos['repos'],
                'inc_repos': inc_repos,
                'period': period,
                'empty': False,
                'version': rx_version}
