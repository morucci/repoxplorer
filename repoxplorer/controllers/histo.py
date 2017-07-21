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

from pecan import conf
from pecan import abort
from pecan import expose

from datetime import datetime

from repoxplorer import index
from repoxplorer.controllers import utils
from repoxplorer.index.commits import Commits
from repoxplorer.index.projects import Projects
from repoxplorer.index.contributors import Contributors

indexname = 'repoxplorer'
xorkey = conf.get('xorkey') or 'default'


class HistoController(object):

    def build_query(self, pid, tid, cid, gid, dfrom, dto,
                    inc_merge_commit, inc_repos,
                    metadata, exc_groups, idents):

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

        mails_to_exclude = {}

        if exc_groups:
            groups_splitted = exc_groups.split(',')
            for gid in groups_splitted:
                _, group = idents.get_group_by_id(gid)
                mails_to_exclude.update(group['emails'])

        projects_index = Projects()
        repos = []

        query_kwargs = {}

        if pid:
            repos = projects_index.get_projects().get(pid)
            if not repos:
                abort(404,
                      detail="The project has not been found")
            query_kwargs.update(
                {'mails': mails_to_exclude,
                 'mails_neg': True})
        elif tid:
            repos = projects_index.get_tags().get(tid)
            if not repos:
                abort(404,
                      detail="The project has not been found")
            query_kwargs.update(
                {'mails': mails_to_exclude,
                 'mails_neg': True})
        elif gid:
            gid, group = idents.get_group_by_id(gid)
            if not group:
                abort(404,
                      detail="The group has not been found")
            mails = group['emails']
            query_kwargs.update({'mails': mails})
        elif cid:
            cid = utils.decrypt(xorkey, cid)
            iid, ident = idents.get_ident_by_id(cid)
            if not ident:
                # No ident has been declared for that contributor
                iid, ident = idents.get_ident_by_email(cid)
            mails = ident['emails']
            query_kwargs.update({'mails': mails})

        p_filter = utils.get_references_filter(repos, inc_repos)

        query_kwargs.update({
            'repos': p_filter,
            'fromdate': dfrom,
            'todate': dto,
            'merge_commit': include_merge_commit,
            'metadata': metadata,
        })

        return query_kwargs

    @expose('json')
    def authors(self, pid=None, tid=None, cid=None, gid=None,
                dfrom=None, dto=None, inc_merge_commit=None,
                inc_repos=None, metadata="", exc_groups=None):

        idents = Contributors()

        query_kwargs = self.build_query(
            pid, tid, cid, gid, dfrom, dto, inc_merge_commit, inc_repos,
            metadata, exc_groups, idents)

        c = Commits(index.Connector(index=indexname))
        if not c.get_commits_amount(**query_kwargs):
            return []
        ret = c.get_authors_histo(**query_kwargs)[1]
        for bucket in ret:
            author_emails = set()
            for author in bucket['authors_email']:
                _, ident = idents.get_ident_by_email(author)
                author_emails.add(ident['default-email'])
            bucket['authors_email'] = list(author_emails)
            bucket['value'] = len(bucket['authors_email'])
            bucket['date'] = bucket['key_as_string']
            del bucket['doc_count']
            del bucket['key_as_string']
            del bucket['key']

        return ret

    @expose('json')
    def commits(self, pid=None, tid=None, cid=None, gid=None,
                dfrom=None, dto=None, inc_merge_commit=None,
                inc_repos=None, metadata="", exc_groups=None):

        idents = Contributors()

        query_kwargs = self.build_query(
            pid, tid, cid, gid, dfrom, dto, inc_merge_commit, inc_repos,
            metadata, exc_groups, idents)

        c = Commits(index.Connector(index=indexname))
        if not c.get_commits_amount(**query_kwargs):
            return []
        ret = c.get_commits_histo(**query_kwargs)
        ret = [{'date': d['key_as_string'],
                'value': d['doc_count']} for d in ret[1]]
        return ret
