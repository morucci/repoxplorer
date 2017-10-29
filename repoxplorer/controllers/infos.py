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

from pecan import expose

from repoxplorer import index
from repoxplorer.controllers import utils
from repoxplorer.index.commits import Commits
from repoxplorer.index.projects import Projects
from repoxplorer.index.contributors import Contributors

indexname = 'repoxplorer'


class InfosController(object):

    def get_generic_infos(self, commits_index, idents, query_kwargs):
        infos = {}
        infos['commits_amount'] = commits_index.get_commits_amount(
            **query_kwargs)
        if not infos['commits_amount']:
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
        return infos

    @expose('json')
    def infos(self, pid=None, tid=None, cid=None, gid=None,
              dfrom=None, dto=None, inc_merge_commit=None,
              inc_repos=None, metadata=None, exc_groups=None):

        c = Commits(index.Connector(index=indexname))
        projects_index = Projects()
        idents = Contributors()

        query_kwargs = utils.resolv_filters(
            projects_index, idents, pid, tid, cid, gid,
            dfrom, dto, inc_repos, inc_merge_commit,
            metadata, exc_groups)

        return self.get_generic_infos(c, idents, query_kwargs)
