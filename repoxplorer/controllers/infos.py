# Copyright 2017, Fabien Boucher
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

from datetime import timedelta

import hashlib

from pecan import abort
from pecan import expose
from pecan import conf

from repoxplorer import index
from repoxplorer.controllers import utils
from repoxplorer.index.commits import Commits
from repoxplorer.index.projects import Projects
from repoxplorer.index.contributors import Contributors

xorkey = conf.get('xorkey') or 'default'


class InfosController(object):

    def get_generic_infos(
            self, projects_index, commits_index, idents, pid, query_kwargs):
        infos = {}
        infos['commits_amount'] = commits_index.get_commits_amount(
            **query_kwargs)
        if not infos['commits_amount']:
            infos['line_modifieds_amount'] = 0
            return infos
        authors = commits_index.get_authors(**query_kwargs)[1]
        infos['authors_amount'] = len(utils.authors_sanitize(idents, authors))
        first, last, duration = commits_index.get_commits_time_delta(
            **query_kwargs)
        infos['first'] = first
        infos['last'] = last
        infos['duration'] = duration
        ttl_average = commits_index.get_ttl_stats(**query_kwargs)[1]['avg']
        infos['ttl_average'] = \
            timedelta(seconds=int(ttl_average)) - timedelta(seconds=0)
        infos['ttl_average'] = int(infos['ttl_average'].total_seconds())

        infos['line_modifieds_amount'] = int(
            commits_index.get_line_modifieds_stats(**query_kwargs)[1]['sum'])

        repos = filter(lambda r: not r.startswith('meta_ref: '),
                       commits_index.get_repos(**query_kwargs)[1])
        if pid:
            projects = (pid,)
        else:
            projects = utils.get_projects_from_references(
                projects_index, repos)
        infos['repos_amount'] = len(repos)
        infos['projects_amount'] = len(projects)
        return infos

    @expose('json')
    @expose('csv:', content_type='text/csv')
    def infos(self, pid=None, tid=None, cid=None, gid=None,
              dfrom=None, dto=None, inc_merge_commit=None,
              inc_repos=None, metadata=None, exc_groups=None,
              inc_groups=None):

        c = Commits(index.Connector())
        projects_index = Projects()
        idents = Contributors()

        query_kwargs = utils.resolv_filters(
            projects_index, idents, pid, tid, cid, gid,
            dfrom, dto, inc_repos, inc_merge_commit,
            metadata, exc_groups, inc_groups)

        return self.get_generic_infos(
            projects_index, c, idents, pid, query_kwargs)

    @expose('json')
    @expose('csv:', content_type='text/csv')
    def contributor(self, cid=None):
        if not cid:
            abort(404,
                  detail="No contributor specified")

        c = Commits(index.Connector())
        idents = Contributors()

        try:
            cid = utils.decrypt(xorkey, cid)
        except Exception:
            abort(404,
                  detail="The cid is incorrectly formated")

        _, ident = idents.get_ident_by_id(cid)
        if not ident:
            # No ident has been declared for that contributor
            ident = idents.get_idents_by_emails(cid).values()[0]
        mails = ident['emails']
        name = ident['name']
        if not name:
            raw_names = c.get_commits_author_name_by_emails([cid])
            if cid not in raw_names:
                # TODO: get_commits_author_name_by_emails must
                # support look by committer email too
                name = 'Unnamed'
            else:
                name = raw_names[cid]

        infos = {}
        infos['name'] = name
        infos['mails_amount'] = len(mails)
        infos['gravatar'] = hashlib.md5(ident['default-email']).hexdigest()
        return infos
