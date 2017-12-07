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

indexname = 'repoxplorer'
xorkey = conf.get('xorkey') or 'default'


class TopAuthorsController(object):

    def top_authors_sanitize(
            self, idents, authors, commits, top):
        sanitized = utils.authors_sanitize(idents, authors)
        top_authors_s = []
        raw_names = {}
        for email, v in sanitized.items():
            top_authors_s.append(
                {'cid': utils.encrypt(xorkey, v[2]),
                 'email': email,
                 'gravatar': hashlib.md5(email.encode('utf-8')).hexdigest(),
                 'amount': int(v[0]),
                 'name': v[1]})
        top_authors_s_sorted = sorted(top_authors_s,
                                      key=lambda k: k['amount'],
                                      reverse=True)[:top]
        name_to_requests = []
        for v in top_authors_s_sorted:
            if not v['name']:
                name_to_requests.append(v['email'])
        if name_to_requests:
            raw_names = commits.get_commits_author_name_by_emails(
                name_to_requests)
        for v in top_authors_s_sorted:
            v['name'] = v['name'] or raw_names[v['email']]
            del v['email']
        return top_authors_s_sorted

    def gbycommits(self, c, idents, query_kwargs):
        top = 25
        authors = c.get_authors(**query_kwargs)[1]
        top_authors = self.top_authors_sanitize(
            idents, authors, c, top)

        return top_authors

    def gbylchanged(self, c, idents, query_kwargs):
        top = 25
        top_authors_modified = c.get_top_authors_by_lines(**query_kwargs)[1]

        top_authors_modified = self.top_authors_sanitize(
            idents, top_authors_modified, c, top)

        return top_authors_modified

    @expose('json')
    @expose('csv:', content_type='text/csv')
    def bylchanged(self, pid=None, tid=None, cid=None, gid=None,
                   dfrom=None, dto=None, inc_merge_commit=None,
                   inc_repos=None, metadata=None, exc_groups=None):

        c = Commits(index.Connector(index=indexname))
        projects_index = Projects()
        idents = Contributors()

        query_kwargs = utils.resolv_filters(
            projects_index, idents, pid, tid, cid, gid,
            dfrom, dto, inc_repos, inc_merge_commit, None, exc_groups)

        return self.gbylchanged(c, idents, query_kwargs)

    @expose('json')
    @expose('csv:', content_type='text/csv')
    def bycommits(self, pid=None, tid=None, cid=None, gid=None,
                  dfrom=None, dto=None, inc_merge_commit=None,
                  inc_repos=None, metadata=None, exc_groups=None):

        c = Commits(index.Connector(index=indexname))
        projects_index = Projects()
        idents = Contributors()

        query_kwargs = utils.resolv_filters(
            projects_index, idents, pid, tid, cid, gid,
            dfrom, dto, inc_repos, inc_merge_commit, None, exc_groups)

        return self.gbycommits(c, idents, query_kwargs)

    @expose('json')
    @expose('csv:', content_type='text/csv')
    def diff(self, pid=None, tid=None, cid=None, gid=None,
             dfrom=None, dto=None, dfromref=None, dtoref=None,
             inc_merge_commit=None, inc_repos=None, metadata=None,
             exc_groups=None):

        if not dfrom or not dto:
            abort(404,
                  detail="Must specify dfrom and dto dates for the new "
                         "contributors")

        if not dfromref or not dtoref:
            abort(404,
                  detail="Must specify dfromref and dto datesref for the "
                         "reference period to compute new contributors")

        # Get contributors for the new period
        c = Commits(index.Connector(index=indexname))
        projects_index = Projects()
        idents = Contributors()

        query_kwargs = utils.resolv_filters(
            projects_index, idents, pid, tid, cid, gid,
            dfrom, dto, inc_repos, inc_merge_commit, None, exc_groups)

        authors_new = self.gbycommits(c, idents, query_kwargs)

        # Now get contributors for the old reference period
        c = Commits(index.Connector(index=indexname))
        projects_index = Projects()
        idents = Contributors()

        query_kwargs = utils.resolv_filters(
            projects_index, idents, pid, tid, cid, gid,
            dfromref, dtoref, inc_repos, inc_merge_commit, None, exc_groups)

        authors_old = self.gbycommits(c, idents, query_kwargs)

        # And compute the difference
        authors_diff = []
        for author in authors_new:
            if author['cid'] not in [aut['cid'] for aut in authors_old
                                     if aut['cid'] == author['cid']]:
                authors_diff.append(author)

        return authors_diff


class TopProjectsController(object):

    def gby(self, ci, pi, query_kwargs,
            inc_repos_detail, project_scope, f1, f2):
        repos = f1(**query_kwargs)[1]
        if project_scope:
            projects = [project_scope]
        else:
            projects = utils.get_projects_from_references(pi, repos)
        if inc_repos_detail:
            repos_contributed = [
                (p, ca) for p, ca in repos.items()]
        else:
            repos_contributed = []
            for pname in projects:
                p_repos = pi.get_projects()[pname]
                p_filter = utils.get_references_filter(p_repos)
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

        return ret

    def gbycommits(self, ci, pi, query_kwargs,
                   inc_repos_detail, project_scope):
        ret = self.gby(ci, pi, query_kwargs, inc_repos_detail, project_scope,
                       ci.get_repos, ci.get_commits_amount)
        return ret

    def gbylchanged(self, ci, pi, query_kwargs,
                    inc_repos_detail, project_scope):

        def f2(**kwargs):
            return ci.get_line_modifieds_stats(**kwargs)[1]['sum']

        ret = self.gby(ci, pi, query_kwargs, inc_repos_detail, project_scope,
                       ci.get_top_repos_by_lines, f2)
        return ret

    @expose('json')
    @expose('csv:', content_type='text/csv')
    def bylchanged(self, pid=None, tid=None, cid=None, gid=None,
                   dfrom=None, dto=None, inc_merge_commit=None,
                   inc_repos=None, metadata=None, exc_groups=None,
                   inc_repos_detail=None, project_scope=None):

        c = Commits(index.Connector(index=indexname))
        projects_index = Projects()
        idents = Contributors()

        query_kwargs = utils.resolv_filters(
            projects_index, idents, pid, tid, cid, gid,
            dfrom, dto, inc_repos, inc_merge_commit, None, exc_groups)

        return self.gbylchanged(c, projects_index, query_kwargs,
                                inc_repos_detail, project_scope)

    @expose('json')
    @expose('csv:', content_type='text/csv')
    def bycommits(self, pid=None, tid=None, cid=None, gid=None,
                  dfrom=None, dto=None, inc_merge_commit=None,
                  inc_repos=None, metadata=None, exc_groups=None,
                  inc_repos_detail=None, project_scope=None):

        c = Commits(index.Connector(index=indexname))
        projects_index = Projects()
        idents = Contributors()

        query_kwargs = utils.resolv_filters(
            projects_index, idents, pid, tid, cid, gid,
            dfrom, dto, inc_repos, inc_merge_commit, None, exc_groups)

        return self.gbycommits(c, projects_index, query_kwargs,
                               inc_repos_detail, project_scope)


class TopsController(object):

    authors = TopAuthorsController()
    projects = TopProjectsController()

    # TODO(fbo): Legacy used be the make templating will be removed
    def top_projects_sanitize(
            self, commits_index, projects_index,
            query_kwargs, inc_repos_detail,
            project_scope=None):
        c_repos = commits_index.get_repos(**query_kwargs)[1]
        lm_repos = commits_index.get_top_repos_by_lines(**query_kwargs)[1]
        if project_scope:
            c_projects = [project_scope]
        else:
            c_projects = utils.get_projects_from_references(
                projects_index, c_repos)

        repos_contributed = {}
        repos_contributed_modified = {}
        if inc_repos_detail:
            repos_contributed = [
                (":".join(p.split(':')[-2:]), ca) for
                p, ca in c_repos.items()]
            repos_contributed_modified = [
                (":".join(p.split(':')[-2:]), int(lm)) for
                p, lm in lm_repos.items()]
        else:
            for pname in c_projects:
                p_repos = projects_index.get_projects()[pname]
                p_filter = utils.get_references_filter(p_repos, None)
                _query_kwargs = copy.deepcopy(query_kwargs)
                _query_kwargs['repos'] = p_filter
                repos_contributed[pname] = commits_index.get_commits_amount(
                    **_query_kwargs)
                repos_contributed_modified[pname] = int(
                    commits_index.get_line_modifieds_stats(
                        **_query_kwargs)[1]['sum'] or 0)

            repos_contributed = [
                (p, ca) for
                p, ca in repos_contributed.items() if ca]
            repos_contributed_modified = [
                (p, lm) for
                p, lm in repos_contributed_modified.items() if lm]

        sorted_repos_contributed = sorted(
            repos_contributed,
            key=lambda i: i[1],
            reverse=True)

        sorted_repos_contributed_modified = sorted(
            repos_contributed_modified,
            key=lambda i: i[1],
            reverse=True)

        return (sorted_repos_contributed, sorted_repos_contributed_modified,
                c_projects, c_repos)
