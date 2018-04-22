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

from pecan import expose

from repoxplorer import index
from repoxplorer.controllers import utils
from repoxplorer.index.commits import Commits
from repoxplorer.index.projects import Projects
from repoxplorer.index.contributors import Contributors


class HistoController(object):

    @expose('json')
    def authors(self, pid=None, tid=None, cid=None, gid=None,
                dfrom=None, dto=None, inc_merge_commit=None,
                inc_repos=None, metadata=None, exc_groups=None,
                inc_groups=None):

        projects_index = Projects()
        idents = Contributors()

        query_kwargs = utils.resolv_filters(
            projects_index, idents, pid, tid, cid, gid,
            dfrom, dto, inc_repos, inc_merge_commit,
            metadata, exc_groups, inc_groups)

        c = Commits(index.Connector())
        if not c.get_commits_amount(**query_kwargs):
            return []
        ret = c.get_authors_histo(**query_kwargs)[1]
        for bucket in ret:
            _idents = idents.get_idents_by_emails(bucket['authors_email'])
            bucket['value'] = len(_idents)
            bucket['date'] = bucket['key_as_string']
            del bucket['authors_email']
            del bucket['doc_count']
            del bucket['key_as_string']
            del bucket['key']

        return ret

    @expose('json')
    def commits(self, pid=None, tid=None, cid=None, gid=None,
                dfrom=None, dto=None, inc_merge_commit=None,
                inc_repos=None, metadata=None, exc_groups=None,
                inc_groups=None):

        projects_index = Projects()
        idents = Contributors()

        query_kwargs = utils.resolv_filters(
            projects_index, idents, pid, tid, cid, gid,
            dfrom, dto, inc_repos, inc_merge_commit,
            metadata, exc_groups, inc_groups)

        c = Commits(index.Connector())
        if not c.get_commits_amount(**query_kwargs):
            return []
        ret = c.get_commits_histo(**query_kwargs)
        ret = [{'date': d['key_as_string'],
                'value': d['doc_count']} for d in ret[1]]
        return ret
