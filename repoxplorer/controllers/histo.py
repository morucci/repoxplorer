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

from pecan import abort
from pecan import expose

from datetime import datetime

from repoxplorer import index
from repoxplorer.controllers import utils
from repoxplorer.index.commits import Commits
from repoxplorer.index.projects import Projects
from repoxplorer.index.contributors import Contributors

indexname = 'repoxplorer'


class HistoController(object):

    @expose('json')
    def authors(self, pid=None, tid=None, cid=None, gid=None,
                start=0, limit=10, htype='authors_count',
                dfrom=None, dto=None, inc_merge_commit=None,
                inc_repos=None, metadata="", exc_groups=None):

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
            dfrom = datetime.strptime(dfrom, "%m/%d/%Y").strftime('%s')
        if dto:
            dto = datetime.strptime(dto, "%m/%d/%Y").strftime('%s')
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

        idents = Contributors()

        mails_to_exclude = {}

        if exc_groups:
            groups_splitted = exc_groups.split(',')
            for gid in groups_splitted:
                _, group = idents.get_group_by_id(gid)
                mails_to_exclude.update(group['emails'])

        projects_index = Projects()
        if pid:
            repos = projects_index.get_projects()[pid]
        else:
            repos = projects_index.get_tags()[tid]

        p_filter = utils.get_references_filter(repos, inc_repos)

        query_kwargs = {
            'repos': p_filter,
            'fromdate': dfrom,
            'mails': mails_to_exclude,
            'mails_neg': True,
            'todate': dto,
            'merge_commit': include_merge_commit,
            'metadata': metadata,
        }

        c = Commits(index.Connector(index=indexname))
        ret = c.get_authors_histo(**query_kwargs)[1]
        utils.histo_authors_sanitize(idents, ret)

        return ret
