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

import copy
import hashlib

from pecan import abort
from pecan import conf
from pecan import expose

from repoxplorer import index
from repoxplorer.controllers import utils
from repoxplorer.index.commits import Commits
from repoxplorer.index.projects import Projects
from repoxplorer.index.contributors import Contributors

xorkey = conf.get('xorkey') or 'default'


class TopAuthorsController(object):

    def resolv_name(self, commits, authors):
        name_to_requests = []
        for v in authors:
            if not v['name']:
                name_to_requests.append(v['email'])
        if name_to_requests:
            raw_names = commits.get_commits_author_name_by_emails(
                name_to_requests)
        for v in authors:
            v['name'] = v['name'] or raw_names[v['email']]
            del v['email']

    def top_authors_sanitize(
            self, idents, authors, commits, top,
            resolv_name=True, clean_email=True):
        sanitized = utils.authors_sanitize(idents, authors)
        top_authors_s = []
        for email, v in sanitized.items():
            top_authors_s.append(
                {'cid': utils.encrypt(xorkey, v[2]),
                 'email': email,
                 'gravatar': hashlib.md5(email.encode('utf-8')).hexdigest(),
                 'amount': int(v[0]),
                 'name': v[1]})
        top_authors_s_sorted = sorted(top_authors_s,
                                      key=lambda k: k['amount'],
                                      reverse=True)
        if top is None:
            top = 10
        else:
            top = int(top)
        # If top set to a negative value all results will be returned
        if top >= 0:
            top_authors_s_sorted = top_authors_s_sorted[:int(top)]

        if resolv_name:
            self.resolv_name(commits, top_authors_s_sorted)

        return top_authors_s_sorted

    def gbycommits(
            self, c, idents, query_kwargs, top,
            resolv_name=True, clean_email=True):
        authors = c.get_authors(**query_kwargs)[1]
        top_authors = self.top_authors_sanitize(
            idents, authors, c, top, resolv_name, clean_email)

        return top_authors

    def gbylchanged(self, c, idents, query_kwargs, top):
        top_authors_modified = c.get_top_authors_by_lines(**query_kwargs)[1]

        top_authors_modified = self.top_authors_sanitize(
            idents, top_authors_modified, c, top)

        return top_authors_modified

    @expose('json')
    @expose('csv:', content_type='text/csv')
    def bylchanged(self, pid=None, tid=None, cid=None, gid=None,
                   dfrom=None, dto=None, inc_merge_commit=None,
                   inc_repos=None, metadata=None, exc_groups=None,
                   limit=None, inc_groups=None):

        c = Commits(index.Connector())
        projects_index = Projects()
        idents = Contributors()

        query_kwargs = utils.resolv_filters(
            projects_index, idents, pid, tid, cid, gid,
            dfrom, dto, inc_repos, inc_merge_commit, metadata,
            exc_groups, inc_groups)

        return self.gbylchanged(c, idents, query_kwargs, limit)

    @expose('json')
    @expose('csv:', content_type='text/csv')
    def bycommits(self, pid=None, tid=None, cid=None, gid=None,
                  dfrom=None, dto=None, inc_merge_commit=None,
                  inc_repos=None, metadata=None, exc_groups=None,
                  limit=None, inc_groups=None):

        c = Commits(index.Connector())
        projects_index = Projects()
        idents = Contributors()

        query_kwargs = utils.resolv_filters(
            projects_index, idents, pid, tid, cid, gid,
            dfrom, dto, inc_repos, inc_merge_commit, metadata,
            exc_groups, inc_groups)

        return self.gbycommits(c, idents, query_kwargs, limit)

    @expose('json')
    @expose('csv:', content_type='text/csv')
    def diff(self, pid=None, tid=None, cid=None, gid=None,
             dfrom=None, dto=None, dfromref=None, dtoref=None,
             inc_merge_commit=None, inc_repos=None, metadata=None,
             exc_groups=None, limit=None, inc_groups=None):

        if not dfrom or not dto:
            abort(404,
                  detail="Must specify dfrom and dto dates for the new "
                         "contributors")

        if not dfromref or not dtoref:
            abort(404,
                  detail="Must specify dfromref and dtoref dates for the "
                         "reference period to compute new contributors")

        # Get contributors for the new period
        c = Commits(index.Connector())
        projects_index = Projects()
        idents = Contributors()

        query_kwargs = utils.resolv_filters(
            projects_index, idents, pid, tid, cid, gid,
            dfrom, dto, inc_repos, inc_merge_commit, metadata,
            exc_groups, inc_groups)

        authors_new = self.gbycommits(
            c, idents, query_kwargs, top=-1,
            resolv_name=False, clean_email=False)

        # Now get contributors for the old reference period
        query_kwargs = utils.resolv_filters(
            projects_index, idents, pid, tid, cid, gid,
            dfromref, dtoref, inc_repos, inc_merge_commit, metadata,
            exc_groups, inc_groups)

        authors_old = self.gbycommits(
            c, idents, query_kwargs, top=-1,
            resolv_name=False, clean_email=False)

        # And compute the difference
        cids_new = set([auth['cid'] for auth in authors_new]) - \
            set([auth['cid'] for auth in authors_old])
        authors_diff = [author for author in authors_new
                        if author['cid'] in cids_new]
        if limit is None:
            limit = 10
        else:
            limit = int(limit)
        # If limit set to a negative value all results will be returned
        if limit >= 0:
            authors_diff = authors_diff[:limit]

        self.resolv_name(c, authors_diff)

        return authors_diff


class TopProjectsController(object):

    def gby(self, ci, pi, query_kwargs,
            inc_repos_detail, f1, f2, limit):
        repos = f1(**query_kwargs)[1]
        if inc_repos_detail:
            repos_contributed = [
                (p, ca) for p, ca in repos.items()
                if not p.startswith('meta_ref: ')]
        else:
            repos_contributed = []
            projects = utils.get_projects_from_references(
                pi, [r for r in repos.keys()
                     if not r.startswith('meta_ref: ')])
            for pname in projects:
                project = pi.get(pname, source=['name', 'meta-ref', 'refs'])
                p_filter = utils.get_references_filter(project)
                _query_kwargs = copy.deepcopy(query_kwargs)
                _query_kwargs['repos'] = p_filter
                ca = int(f2(**_query_kwargs) or 0)
                if ca:
                    repos_contributed.append((pname, ca))

        sorted_rc = sorted(repos_contributed,
                           key=lambda i: i[1],
                           reverse=True)
        ret = []
        for item in sorted_rc:
            ret.append({"amount": int(item[1])})
            if inc_repos_detail:
                ret[-1]["projects"] = utils.get_projects_from_references(
                    pi, [item[0]])
            ret[-1]["name"] = ":".join(item[0].split(':')[-2:])

        if limit is None:
            limit = 10
        else:
            limit = int(limit)
        # If limit set to a negative value all results will be returned
        if limit >= 0:
            ret = ret[:limit]
        return ret

    def gbycommits(self, ci, pi, query_kwargs, inc_repos_detail, limit):
        ret = self.gby(ci, pi, query_kwargs, inc_repos_detail,
                       ci.get_repos, ci.get_commits_amount, limit)
        return ret

    def gbylchanged(self, ci, pi, query_kwargs, inc_repos_detail, limit):

        def f2(**kwargs):
            return ci.get_line_modifieds_stats(**kwargs)[1]['sum']

        ret = self.gby(ci, pi, query_kwargs, inc_repos_detail,
                       ci.get_top_repos_by_lines, f2, limit)
        return ret

    @expose('json')
    @expose('csv:', content_type='text/csv')
    def bylchanged(self, pid=None, tid=None, cid=None, gid=None,
                   dfrom=None, dto=None, inc_merge_commit=None,
                   inc_repos=None, metadata=None, exc_groups=None,
                   inc_repos_detail=None, inc_groups=None, limit=None):

        c = Commits(index.Connector())
        projects_index = Projects()
        idents = Contributors()

        query_kwargs = utils.resolv_filters(
            projects_index, idents, pid, tid, cid, gid,
            dfrom, dto, inc_repos, inc_merge_commit, metadata,
            exc_groups, inc_groups)

        return self.gbylchanged(c, projects_index, query_kwargs,
                                inc_repos_detail, limit)

    @expose('json')
    @expose('csv:', content_type='text/csv')
    def bycommits(self, pid=None, tid=None, cid=None, gid=None,
                  dfrom=None, dto=None, inc_merge_commit=None,
                  inc_repos=None, metadata=None, exc_groups=None,
                  inc_repos_detail=None, inc_groups=None, limit=None):

        c = Commits(index.Connector())
        projects_index = Projects()
        idents = Contributors()

        query_kwargs = utils.resolv_filters(
            projects_index, idents, pid, tid, cid, gid,
            dfrom, dto, inc_repos, inc_merge_commit, metadata,
            exc_groups, inc_groups)

        return self.gbycommits(c, projects_index, query_kwargs,
                               inc_repos_detail, limit)


class TopsController(object):

    authors = TopAuthorsController()
    projects = TopProjectsController()
