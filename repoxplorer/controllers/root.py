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

    def top_authors_sanitize(self, top_authors):
        idents = Users().get_users()
        sanitized = {}
        for k, v in top_authors[1].items():
            if k in idents:
                main_email = idents[k][0]
                name = idents[k][1]
            else:
                main_email = k
                name = v[1]
            amount = int(v[0])
            if main_email in sanitized:
                sanitized[main_email][0] += amount
            else:
                sanitized[main_email] = [amount, name]
        top_authors_s = []
        for k, v in sanitized.items():
            top_authors_s.append(
                {'email': k,
                 'gravatar': hashlib.md5(k).hexdigest(),
                 'amount': v[0],
                 'name': v[1]})
        top_authors_s_sorted = sorted(top_authors_s,
                                      key=lambda k: k['amount'],
                                      reverse=True)
        return top_authors_s_sorted

    def top_authors_modified_sanitize(self, top_authors_modified,
                                      commits, top_amount=25):
        idents = Users().get_users()
        top_authors_modified_s = []
        sanitized = {}
        for k, v in top_authors_modified[1].items():
            if k in idents:
                main_email = idents[k][0]
                name = idents[k][1]
            else:
                main_email = k
                name = None
            amount = int(v)
            if main_email in sanitized:
                sanitized[main_email][0] += amount
            else:
                sanitized[main_email] = [amount, name]
        for k, v in sanitized.items():
            top_authors_modified_s.append(
                {'email': k,
                 'gravatar': hashlib.md5(k).hexdigest(),
                 'amount': v[0],
                 'name': v[1]})
        top_authors_modified_s_sorted = sorted(
            top_authors_modified_s,
            key=lambda k: k['amount'],
            reverse=True)[:top_amount]
        top_authors_modified_s_sorted = top_authors_modified_s_sorted
        for author in top_authors_modified_s_sorted:
            # Get author name if not known in ident
            if author['name']:
                continue
            author['name'] = commits.get_commits(
                [author['email']], [], limit=1)[2][0]['author_name']
        return top_authors_modified_s_sorted

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
        p_filter = []
        for p in project:
            if inc_projects:
                if not "%s:%s" % (p['name'], p['branch']) in inc_projects:
                    continue
            p_filter.append("%s:%s:%s" % (p['uri'],
                                          p['name'],
                                          p['branch']))

        commits_amount = c.get_commits_amount(
            projects=p_filter,
            fromdate=dfrom,
            todate=dto,
            merge_commit=include_merge_commit)

        if not commits_amount:
            # No commit found
            return {'pid': pid,
                    'inc_merge_commit': inc_merge_commit,
                    'period': (odfrom, odto),
                    'subprojects': project,
                    'inc_projects': inc_projects,
                    'empty': True}

        histo = c.get_commits_histo(projects=p_filter,
                                    fromdate=dfrom,
                                    todate=dto,
                                    merge_commit=include_merge_commit)
        histo = [{'date': d['key_as_string'],
                  'value': d['doc_count']} for d in histo[1]]

        top_authors = c.get_top_authors(projects=p_filter,
                                        fromdate=dfrom,
                                        todate=dto,
                                        merge_commit=include_merge_commit)
        top_authors_modified = c.get_top_authors_by_lines(
            projects=p_filter,
            fromdate=dfrom,
            todate=dto,
            merge_commit=include_merge_commit)

        top_authors = self.top_authors_sanitize(top_authors)
        top_authors_modified = self.top_authors_modified_sanitize(
            top_authors_modified, c, top_amount=25)

        first, last, duration = c.get_commits_time_delta(
            projects=p_filter,
            fromdate=dfrom,
            todate=dto,
            merge_commit=include_merge_commit)

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
        p_filter = []
        for p in project:
            if inc_projects:
                if not "%s:%s" % (p['name'], p['branch']) in inc_projects:
                    continue
            p_filter.append("%s:%s:%s" % (p['uri'],
                                          p['name'],
                                          p['branch']))
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
            # Request the ident index to fetch author/committer name
            for elm in ('author', 'committer'):
                if idents.get(cmt['%s_email' % elm]):
                    cmt['%s_name' % elm] = idents.get(cmt['%s_email' % elm])[1]
            # Convert the TTL to something human readable
            cmt['ttl'] = str((datetime.fromtimestamp(cmt['ttl']) -
                              datetime.fromtimestamp(0)))
        return resp
