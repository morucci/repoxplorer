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


import json
import copy
import hashlib

from pecan import expose
from pecan import abort
from pecan import conf

from datetime import datetime
from datetime import timedelta

from repoxplorer.controllers import utils
from repoxplorer import index
from repoxplorer.index.commits import Commits
from repoxplorer.index.commits import PROPERTIES
from repoxplorer.index.projects import Projects
from repoxplorer.index.contributors import Contributors
from repoxplorer.index.tags import Tags


indexname = 'repoxplorer'
xorkey = conf.get('xorkey') or 'default'


class RootController(object):

    def get_projects_from_repos_list(self, projects, c_repos):
        c_projects = []
        for pname, repos in projects.items():
            for r in repos:
                pid = "%s:%s:%s" % (r['uri'],
                                    r['name'],
                                    r['branch'])
                if pid in c_repos and pname not in c_projects:
                    c_projects.append(pname)
        return c_projects

    def get_repos_filter(self, repos, inc_repos):
        p_filter = []
        for p in repos:
            if inc_repos:
                if not "%s:%s" % (p['name'], p['branch']) in inc_repos:
                    continue
            p_filter.append("%s:%s:%s" % (p['uri'],
                                          p['name'],
                                          p['branch']))
        return p_filter

    def get_mail_filter(self, idents, cid):
        ident = idents.get_ident_by_id(cid)
        if not ident[1]:
            # No ident has been declared for that contributor
            ident = idents.get_ident_by_email(cid)
        return ident[1]['emails'].keys()

    @expose(template='index.html')
    def index(self):
        projects = Projects().get_projects()
        tags = Projects().tags.keys()
        return {'projects': projects,
                'tags': tags}

    @expose('json')
    def projects(self):
        projects = Projects().get_projects()
        tags = Projects().tags.keys()
        return {'projects': projects,
                'tags': tags}

    @expose(template='contributors.html')
    def contributors(self, search=""):
        max_result = 50
        c = Commits(index.Connector(index=indexname))
        raw_conts = c.get_authors(merge_commit=False)
        conts = self.top_authors_sanitize(raw_conts, c)
        total_contributors = len(conts)
        conts = [co for co in conts
                 if co['name'].lower().find(search.lower()) >= 0]
        return {'contributors': conts[:max_result],
                'total_contributors': total_contributors,
                'total_hits': len(conts),
                'max_result': max_result,
                'search': search}

    @expose(template='contributor.html')
    def contributor(self, cid, dfrom=None, dto=None,
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
                dfrom, "%m/%d/%Y").strftime('%s')
        if dto:
            dto = datetime.strptime(
                dto, "%m/%d/%Y").strftime('%s')
        c = Commits(index.Connector(index=indexname))
        idents = Contributors()
        iid, ident = idents.get_ident_by_id(cid)
        if not ident:
            # No ident has been declared for that contributor
            iid, ident = idents.get_ident_by_email(cid)
        mails = ident['emails']
        name = ident['name']
        if not name:
            raw_names = c.get_commits_author_name_by_emails([cid])
            name = raw_names[cid]

        query_kwargs = {
            'fromdate': dfrom,
            'todate': dto,
            'mails': mails,
            'merge_commit': include_merge_commit,
        }

        if dfrom is None or dto is None:
            period = (None, None)
        else:
            period = (datetime.fromtimestamp(float(dfrom)),
                      datetime.fromtimestamp(float(dto)))

        commits_amount = c.get_commits_amount(**query_kwargs)

        if not commits_amount:
            # No commit found
            return {'name': name,
                    'gravatar': hashlib.md5(
                        ident['default-email']).hexdigest(),
                    'cid': utils.encrypt(xorkey, cid),
                    'period': period,
                    'empty': True}

        projects = Projects().get_projects()
        c_repos = c.get_repos(**query_kwargs)[1]
        lm_repos = c.get_top_repos_by_lines(**query_kwargs)[1]
        c_projects = self.get_projects_from_repos_list(projects, c_repos)

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
                p_repos = projects[pname]
                p_filter = self.get_repos_filter(p_repos, None)
                _query_kwargs = copy.deepcopy(query_kwargs)
                _query_kwargs['repos'] = p_filter
                repos_contributed[pname] = c.get_commits_amount(
                    **_query_kwargs)
                repos_contributed_modified[pname] = int(
                    c.get_line_modifieds_stats(**_query_kwargs)[1]['sum'])

            repos_contributed = [
                (p, ca) for
                p, ca in repos_contributed.items()]
            repos_contributed_modified = [
                (p, lm) for
                p, lm in repos_contributed_modified.items()]

        sorted_repos_contributed = sorted(
            repos_contributed,
            key=lambda i: i[1],
            reverse=True)

        sorted_repos_contributed_modified = sorted(
            repos_contributed_modified,
            key=lambda i: i[1],
            reverse=True)

        ttl_average = c.get_ttl_stats(**query_kwargs)[1]['avg']
        ttl_average = timedelta(
            seconds=int(ttl_average)) - timedelta(seconds=0)

        first, last, duration = c.get_commits_time_delta(**query_kwargs)

        histo = c.get_commits_histo(**query_kwargs)
        histo = [{'date': d['key_as_string'],
                  'value': d['doc_count']} for d in histo[1]]

        line_modifieds_amount = int(c.get_line_modifieds_stats(
            **query_kwargs)[1]['sum'])

        return {'name': name,
                'gravatar': hashlib.md5(ident['default-email']).hexdigest(),
                'histo': json.dumps(histo),
                'commits_amount': commits_amount,
                'line_modifieds_amount': line_modifieds_amount,
                'period': period,
                'repos': sorted_repos_contributed,
                'repos_line_mdfds': sorted_repos_contributed_modified,
                'projects_amount': len(c_projects),
                'repos_amount': len(c_repos),
                'known_emails_amount': len(mails),
                'first': datetime.fromtimestamp(first),
                'last': datetime.fromtimestamp(last),
                'duration': (datetime.fromtimestamp(duration) -
                             datetime.fromtimestamp(0)),
                'ttl_average': ttl_average,
                'cid': utils.encrypt(xorkey, cid),
                'empty': False}

    def top_authors_sanitize(self, top_authors, commits, top=100000):
        idents = Contributors()
        sanitized = {}
        for email, v in top_authors[1].items():
            iid, ident = idents.get_ident_by_email(email)
            main_email = ident['default-email']
            name = ident['name']
            if main_email in sanitized:
                sanitized[main_email][0] += v
            else:
                sanitized[main_email] = [v, name, iid]
        top_authors_s = []
        raw_names = {}
        for email, v in sanitized.items():
            top_authors_s.append(
                {'cid': utils.encrypt(xorkey, v[2]),
                 'email': email,
                 'gravatar': hashlib.md5(email).hexdigest(),
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

    @expose(template='project.html')
    def project(self, pid=None, tid=None, dfrom=None, dto=None,
                inc_merge_commit=None, inc_repos=None, metadata=None):
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
        c = Commits(index.Connector(index=indexname))
        if pid:
            repos = Projects().get_projects()[pid]
        else:
            repos = Projects().get_repos_by_tag(tid)
        p_filter = self.get_repos_filter(repos, inc_repos)

        query_kwargs = {
            'repos': p_filter,
            'fromdate': dfrom,
            'todate': dto,
            'merge_commit': include_merge_commit,
            'metadata': metadata,
        }

        commits_amount = c.get_commits_amount(**query_kwargs)

        if dfrom is None or dto is None:
            period = (None, None)
        else:
            period = (datetime.fromtimestamp(float(dfrom)),
                      datetime.fromtimestamp(float(dto)))

        if not commits_amount:
            # No commit found
            return {'pid': pid,
                    'tid': tid,
                    'period': period,
                    'repos': repos,
                    'inc_repos': inc_repos,
                    'empty': True}

        histo = c.get_commits_histo(**query_kwargs)
        histo = [{'date': d['key_as_string'],
                  'value': d['doc_count']} for d in histo[1]]

        top_authors = c.get_authors(**query_kwargs)
        top_authors_modified = c.get_top_authors_by_lines(**query_kwargs)

        authors_amount = len(top_authors[1])

        top_authors = self.top_authors_sanitize(
            top_authors, c, top=25)
        top_authors_modified = self.top_authors_sanitize(
            top_authors_modified, c, top=25)

        first, last, duration = c.get_commits_time_delta(**query_kwargs)

        ttl_average = c.get_ttl_stats(**query_kwargs)[1]['avg']
        ttl_average = timedelta(
            seconds=int(ttl_average)) - timedelta(seconds=0)

        return {'pid': pid,
                'tid': tid,
                'histo': json.dumps(histo),
                'top_authors': top_authors,
                'top_authors_modified': top_authors_modified,
                'authors_amount': authors_amount,
                'commits_amount': commits_amount,
                'first': datetime.fromtimestamp(first),
                'last': datetime.fromtimestamp(last),
                'duration': (datetime.fromtimestamp(duration) -
                             datetime.fromtimestamp(0)),
                'repos': repos,
                'inc_repos': inc_repos,
                'period': period,
                'ttl_average': ttl_average,
                'empty': False}

    def resolv_filters(self, projects_index, idents, pid,
                       tid, cid, dfrom, dto, inc_repos,
                       inc_merge_commit):

        if pid:
            project = projects_index.get_projects()[pid]
            p_filter = self.get_repos_filter(project, inc_repos)
        elif tid:
            project = Projects().get_repos_by_tag(tid)
            p_filter = self.get_repos_filter(project, inc_repos)
        else:
            p_filter = []

        if cid:
            cid = utils.decrypt(xorkey, cid)
            mails = self.get_mail_filter(idents, cid)
        else:
            mails = []

        if dfrom:
            dfrom = datetime.strptime(
                dfrom, "%m/%d/%Y").strftime('%s')

        if dto:
            dto = datetime.strptime(
                dto, "%m/%d/%Y").strftime('%s')

        if inc_merge_commit == 'on':
            # The None value will return all whatever
            # the commit is a merge one or not
            inc_merge_commit = None
        else:
            inc_merge_commit = False

        return p_filter, mails, dfrom, dto, inc_merge_commit

    @expose('json')
    def metadata(self, key=None, pid=None, tid=None, cid=None,
                 dfrom=None, dto=None, inc_merge_commit=None,
                 inc_repos=None):
        c = Commits(index.Connector(index=indexname))
        projects_index = Projects()
        idents = Contributors()
        p_filter, mails, dfrom, dto, inc_merge_commit = self.resolv_filters(
            projects_index, idents,
            pid, tid, cid, dfrom, dto, inc_repos,
            inc_merge_commit)

        if not key:
            keys = c.get_metadata_keys(
                mails, p_filter, dfrom, dto, inc_merge_commit)
            return keys
        else:
            vals = c.get_metadata_key_values(
                key, mails, p_filter, dfrom, dto, inc_merge_commit)
            return vals

    @expose('json')
    def tags(self, pid=None, tid=None,
             dfrom=None, dto=None, inc_repos=None):
        t = Tags(index.Connector(index=indexname))
        projects_index = Projects()
        p_filter, _, dfrom, dto, _ = self.resolv_filters(
            projects_index, None,
            pid, tid, None, dfrom, dto, inc_repos, None)
        p_filter = [":".join(r.split(':')[:-1]) for r in p_filter]
        ret = [r['_source'] for r in t.get_tags(p_filter, dfrom, dto)]
        # TODO: if tid is given we can include user defined releases
        # for repo tagged with tid.
        if not pid:
            return ret
        # now append user defined releases
        ur = {}
        project = projects_index.get_projects()[pid]
        for repo in project:
            if 'releases' in repo:
                for release in repo['releases']:
                    ur[release['name']] = {'name': release['name'],
                                           'date': release['date'],
                                           'repo': release['repo']}
        for rel in ur.values():
            ret.append(rel)
        return ret

    @expose('json')
    def commits(self, pid=None, tid=None, cid=None, start=0, limit=10,
                dfrom=None, dto=None, inc_merge_commit=None,
                inc_repos=None, metadata=""):
        c = Commits(index.Connector(index=indexname))
        projects_index = Projects()
        idents = Contributors()
        _metadata = []
        metadata_splitted = metadata.split(',')
        for meta in metadata_splitted:
            try:
                key, value = meta.split(':')
                if value == '*':
                    value = None
            except ValueError:
                continue
            _metadata.append((key, value))

        p_filter, mails, dfrom, dto, inc_merge_commit = self.resolv_filters(
            projects_index, idents,
            pid, tid, cid, dfrom, dto, inc_repos,
            inc_merge_commit)

        resp = c.get_commits(repos=p_filter, mails=mails,
                             fromdate=dfrom, todate=dto,
                             start=start, limit=limit,
                             merge_commit=inc_merge_commit,
                             metadata=_metadata)
        for cmt in resp[2]:
            # Get extra metadata keys
            extra = set(cmt.keys()) - set(PROPERTIES.keys())
            cmt['metadata'] = list(extra)
            # Compute link to access commit diff based on the
            # URL template provided in projects.yaml
            cmt['gitwebs'] = [projects_index.get_gitweb_link(
                              ":".join(p.split(':')[0:-1])) %
                              {'sha': cmt['sha']} for
                              p in cmt['repos']]
            # Remove to verbose details mentionning this commit belong
            # to repos not included in the search
            # Also remove the URI part
            cmt['repos'] = [":".join(p.split(':')[-2:]) for
                            p in cmt['repos']]
            # Request the ident index to fetch author/committer name/email
            for elm in ('author', 'committer'):
                _, c_data = idents.get_ident_by_email(cmt['%s_email' % elm])
                cmt['%s_email' % elm] = c_data['default-email']
                if c_data['name']:
                    cmt['%s_name' % elm] = c_data['name']
            # Convert the TTL to something human readable
            cmt['ttl'] = str((datetime.fromtimestamp(cmt['ttl']) -
                              datetime.fromtimestamp(0)))
            cmt['author_gravatar'] = \
                hashlib.md5(cmt['author_email']).hexdigest()
            cmt['committer_gravatar'] = \
                hashlib.md5(cmt['committer_email']).hexdigest()
            if len(cmt['commit_msg']) > 80:
                cmt['commit_msg'] = cmt['commit_msg'][0:76] + '...'
            # Add cid and ccid
            cmt['cid'] = utils.encrypt(xorkey, cmt['author_email'])
            cmt['ccid'] = utils.encrypt(xorkey, cmt['committer_email'])
            # Remove email details
            del cmt['author_email']
            del cmt['committer_email']
        return resp
