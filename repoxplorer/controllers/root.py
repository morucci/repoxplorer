# Copyright 2016, Fabien Boucher
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


import json
import hashlib

from pecan import expose

from datetime import datetime
from datetime import timedelta

from repoxplorer import index
from repoxplorer.index.commits import Commits
from repoxplorer.index.projects import Projects
from repoxplorer.index.users import Users


indexname = 'repoxplorer'


class RootController(object):

    @expose(template='index.html')
    def index(self):
        projects = Projects().get_projects()
        return {'projects': projects}

    @expose(template='contributors.html')
    def contributors(self):
        c = Commits(index.Connector(index=indexname))
        raw_conts = c.get_authors(merge_commit=False)
        conts = self.top_authors_sanitize(raw_conts, c)
        return {'contributors': conts}

    @expose(template='contributor.html')
    def contributor(self, cid):
        c = Commits(index.Connector(index=indexname))
        idents = Users().get_users()
        if cid in idents:
            mails = idents[cid][2]
            name = idents[cid][1]
        else:
            mails = [cid]
            raw_names = c.get_commits_author_name_by_emails([cid])
            name = raw_names[cid]
        commits_amount = c.get_commits_amount(mails=mails)

        query_kwargs = {
            'fromdate': None,
            'todate': None,
            'mails': mails,
            'merge_commit': False,
        }

        projects = Projects().get_projects()

        c_subprojects = c.get_projects(**query_kwargs)[1]
        projects_contributed = {}

        lm_subprojects = c.get_top_projects_by_lines(**query_kwargs)[1]
        projects_contributed_modified = {}

        for pname, subprojects in projects.items():
            for p in subprojects:
                pid = "%s:%s:%s" % (p['uri'],
                                    p['name'],
                                    p['branch'])
                if pid in c_subprojects:
                    projects_contributed.setdefault(pname, 0)
                    projects_contributed[pname] += c_subprojects[pid]
                if pid in lm_subprojects:
                    projects_contributed_modified.setdefault(pname, 0)
                    projects_contributed_modified[pname] += lm_subprojects[pid]

        projects_contributed = [
            (p, ca) for p, ca in projects_contributed.items()]
        sorted_projects_contributed = sorted(
            projects_contributed,
            key=lambda i: i[1],
            reverse=True)

        projects_contributed_modified = [
            (p, lm) for p, lm in projects_contributed_modified.items()]
        sorted_projects_contributed_modified = sorted(
            projects_contributed_modified,
            key=lambda i: i[1],
            reverse=True)

        histo = c.get_commits_histo(**query_kwargs)
        histo = [{'date': d['key_as_string'],
                  'value': d['doc_count']} for d in histo[1]]

        return {'name': name,
                'histo': json.dumps(histo),
                'commits_amount': commits_amount,
                'projects': sorted_projects_contributed,
                'projects_line_mdfds': sorted_projects_contributed_modified,
                'projects_amount': len(sorted_projects_contributed),
                'known_emails_amount': len(mails),
                'cid': cid}

    def top_authors_sanitize(self, top_authors, commits):
        idents = Users().get_users()
        sanitized = {}
        name_to_requests = []
        for k, v in top_authors[1].items():
            if k in idents:
                main_email = idents[k][0]
                name = idents[k][1]
            else:
                main_email = k
                name = None
                name_to_requests.append(main_email)
            if main_email in sanitized:
                sanitized[main_email][0] += v
            else:
                sanitized[main_email] = [v, name]
        top_authors_s = []
        raw_names = {}
        if name_to_requests:
            raw_names = commits.get_commits_author_name_by_emails(
                name_to_requests)
        for k, v in sanitized.items():
            top_authors_s.append(
                {'email': k,
                 'gravatar': hashlib.md5(k).hexdigest(),
                 'amount': v[0],
                 'name': v[1] or raw_names[k]})
        top_authors_s_sorted = sorted(top_authors_s,
                                      key=lambda k: k['amount'],
                                      reverse=True)
        return top_authors_s_sorted

    def top_authors_modified_sanitize(self, top_authors_modified,
                                      commits, top_amount=25):
        idents = Users().get_users()
        top_authors_modified_s = []
        sanitized = {}
        name_to_requests = []
        for k, v in top_authors_modified[1].items():
            if k in idents:
                main_email = idents[k][0]
                name = idents[k][1]
            else:
                main_email = k
                name = None
                name_to_requests.append(main_email)
            amount = int(v)
            if main_email in sanitized:
                sanitized[main_email][0] += amount
            else:
                sanitized[main_email] = [amount, name]
        raw_names = {}
        if name_to_requests:
            raw_names = commits.get_commits_author_name_by_emails(
                name_to_requests)
        for k, v in sanitized.items():
            top_authors_modified_s.append(
                {'email': k,
                 'gravatar': hashlib.md5(k).hexdigest(),
                 'amount': v[0],
                 'name': v[1] or raw_names[k]})
        top_authors_modified_s_sorted = sorted(
            top_authors_modified_s,
            key=lambda k: k['amount'],
            reverse=True)[:top_amount]
        top_authors_modified_s_sorted = top_authors_modified_s_sorted
        return top_authors_modified_s_sorted

    def get_project_filter(self, project, inc_projects):
        p_filter = []
        for p in project:
            if inc_projects:
                if not "%s:%s" % (p['name'], p['branch']) in inc_projects:
                    continue
            p_filter.append("%s:%s:%s" % (p['uri'],
                                          p['name'],
                                          p['branch']))
        return p_filter

    @expose(template='project.html')
    def project(self, pid, dfrom=None, dto=None,
                inc_merge_commit=None, inc_projects=None):
        if inc_merge_commit != 'on':
            inc_merge_commit = ''
            include_merge_commit = False
        else:
            # The None value will return all whatever
            # the commit is a merge one or not
            include_merge_commit = None
        odfrom = None
        odto = None
        if dfrom:
            odfrom = dfrom
            dfrom = datetime.strptime(
                dfrom, "%m/%d/%Y").strftime('%s')
        if dto:
            odto = dto
            dto = datetime.strptime(
                dto, "%m/%d/%Y").strftime('%s')
        c = Commits(index.Connector(index=indexname))
        projects = Projects().get_projects()
        project = projects[pid]
        p_filter = self.get_project_filter(project, inc_projects)

        query_kwargs = {
            'projects': p_filter,
            'fromdate': dfrom,
            'todate': dto,
            'merge_commit': include_merge_commit,
        }

        commits_amount = c.get_commits_amount(**query_kwargs)

        if not commits_amount:
            # No commit found
            return {'pid': pid,
                    'inc_merge_commit': inc_merge_commit,
                    'period': (odfrom, odto),
                    'subprojects': project,
                    'inc_projects': inc_projects,
                    'empty': True}

        histo = c.get_commits_histo(**query_kwargs)
        histo = [{'date': d['key_as_string'],
                  'value': d['doc_count']} for d in histo[1]]

        top_authors = c.get_authors(**query_kwargs)
        top_authors_modified = c.get_top_authors_by_lines(**query_kwargs)

        top_authors = self.top_authors_sanitize(top_authors, c)
        top_authors_modified = self.top_authors_modified_sanitize(
            top_authors_modified, c, top_amount=25)

        first, last, duration = c.get_commits_time_delta(**query_kwargs)

        ttl_average = c.get_ttl_stats(**query_kwargs)[1]['avg']
        ttl_average = timedelta(
            seconds=int(ttl_average)) - timedelta(seconds=0)

        return {'pid': pid,
                'histo': json.dumps(histo),
                'top_authors': top_authors[:25],
                'top_authors_modified': top_authors_modified,
                'authors_amount': len(top_authors),
                'commits_amount': commits_amount,
                'first': datetime.fromtimestamp(first),
                'last': datetime.fromtimestamp(last),
                'duration': (datetime.fromtimestamp(duration) -
                             datetime.fromtimestamp(0)),
                'subprojects': project,
                'inc_merge_commit': inc_merge_commit,
                'inc_projects': inc_projects,
                'period': (odfrom, odto),
                'ttl_average': ttl_average,
                'empty': False}

    @expose('json')
    def commits(self, pid, mails=None, start=0, limit=10,
                dfrom=None, dto=None, inc_merge_commit=None,
                inc_projects=None):
        c = Commits(index.Connector(index=indexname))
        projects_index = Projects()
        idents = Users().get_users()
        project = projects_index.get_projects()[pid]
        if inc_merge_commit == 'on':
            # The None value will return all whatever
            # the commit is a merge one or not
            inc_merge_commit = None
        else:
            inc_merge_commit = False

        p_filter = self.get_project_filter(project, inc_projects)

        if mails:
            mails = mails.split('+')
        else:
            mails = []
        if dfrom:
            dfrom = datetime.strptime(
                dfrom, "%m/%d/%Y").strftime('%s')
        if dto:
            dto = datetime.strptime(
                dto, "%m/%d/%Y").strftime('%s')
        resp = c.get_commits(projects=p_filter, mails=mails,
                             fromdate=dfrom, todate=dto,
                             start=start, limit=limit,
                             merge_commit=inc_merge_commit)
        for cmt in resp[2]:
            # Compute link to access commit diff based on the
            # URL template provided in projects.yaml
            cmt['gitwebs'] = [projects_index.get_gitweb_link(
                              ":".join(p.split(':')[0:-1])) %
                              {'sha': cmt['sha']} for
                              p in cmt['projects'] if p in p_filter]
            # Remove to verbose details mentionning this commit belong
            # to projects not included in the search
            # Also remove the URI part
            cmt['projects'] = [":".join(p.split(':')[-2:]) for
                               p in cmt['projects'] if p in p_filter]
            # Request the ident index to fetch author/committer name/email
            for elm in ('author', 'committer'):
                if idents.get(cmt['%s_email' % elm]):
                    cmt['%s_name' % elm] = idents.get(
                        cmt['%s_email' % elm])[1]
                    cmt['%s_email' % elm] = idents.get(
                        cmt['%s_email' % elm])[0]
            # Convert the TTL to something human readable
            cmt['ttl'] = str((datetime.fromtimestamp(cmt['ttl']) -
                              datetime.fromtimestamp(0)))
            cmt['author_gravatar'] = \
                hashlib.md5(cmt['author_email']).hexdigest()
            cmt['committer_gravatar'] = \
                hashlib.md5(cmt['committer_email']).hexdigest()
            if len(cmt['commit_msg']) > 80:
                cmt['commit_msg'] = cmt['commit_msg'][0:76] + '...'
        return resp
