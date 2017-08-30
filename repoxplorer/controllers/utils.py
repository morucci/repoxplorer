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

import copy
import base64
import hashlib
from Crypto.Cipher import XOR
from pecan import conf
from pecan import abort
from datetime import datetime
from datetime import timedelta
from collections import OrderedDict

xorkey = conf.get('xorkey') or 'default'


def encrypt(key, plaintext):
    cipher = XOR.new(key)
    return base64.b64encode(
        cipher.encrypt(plaintext.encode('utf-8'))).replace('=', '-')


def decrypt(key, ciphertext):
    cipher = XOR.new(key)
    return cipher.decrypt(base64.b64decode(ciphertext.replace('-', '=')))


def get_projects_from_references(projects, c_references):
    c_projects = set()
    for pname, details in projects.items():
        for r in details['repos']:
            rid = "%s:%s:%s" % (r['uri'],
                                r['name'],
                                r['branch'])
            if rid in c_references:
                c_projects.add(pname)
    return c_projects


def get_references_filter(project, inc_references=None):
    r_filter = {}
    if "repos" in project:
        for r in project['repos']:
            if inc_references:
                if not "%(name)s:%(branch)s" % r in inc_references:
                    continue
                r_filter["%(uri)s:%(name)s:%(branch)s" % r] = r.get('paths')
    return r_filter


def get_mail_filter(idents, cid=None, gid=None):
    if cid:
        ident = idents.get_ident_by_id(cid)
        if not ident[1]:
            # No ident has been declared for that contributor
            ident = idents.get_ident_by_email(cid)
        return ident[1]['emails']
    elif gid:
        gid, group = idents.get_group_by_id(gid)
        if not group:
            abort(404,
                  detail="The group has not been found")
        return group['emails']
    else:
        return {}


def resolv_filters(projects_index, idents, pid,
                   tid, cid, gid, dfrom, dto, inc_repos,
                   inc_merge_commit):

    if pid:
        project = projects_index.get_projects().get(pid)
        if not project:
            abort(404,
                  detail="The project has not been found")
        p_filter = get_references_filter(project, inc_repos)
    elif tid:
        project = projects_index.get_tags().get(tid)
        if not project:
            abort(404,
                  detail="The project has not been found")
        p_filter = get_references_filter(project, inc_repos)
    else:
        p_filter = []

    mails = []
    domains = []
    if cid or gid:
        if cid:
            cid = decrypt(xorkey, cid)
        mails = get_mail_filter(idents, cid, gid)
        if gid:
            _, group = idents.get_group_by_id(gid)
            domains.extend(group.get('domains', []))

    if dfrom:
        dfrom = datetime.strptime(dfrom, "%Y-%m-%d").strftime('%s')

    if dto:
        dto = datetime.strptime(dto, "%Y-%m-%d").strftime('%s')

    if inc_merge_commit == 'on':
        # The None value will return all whatever
        # the commit is a merge one or not
        inc_merge_commit = None
    else:
        inc_merge_commit = False

    return p_filter, mails, dfrom, dto, inc_merge_commit, domains


def search_authors_sanitize(idents, authors):
    result = {}
    for email, name in authors.items():
        iid, ident = idents.get_ident_by_email(email)
        email = ident['default-email']
        name = ident['name'] or name
        result[encrypt(xorkey, iid)] = {
            'name': name,
            'gravatar': hashlib.md5(email.encode('utf-8')).hexdigest()}
    result = OrderedDict(
        sorted(result.items(), key=lambda t: t[0]))
    return result


def top_authors_sanitize(idents, top_authors, commits, top=100000):
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
            {'cid': encrypt(xorkey, v[2]),
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


def get_generic_infos(commits_index, query_kwargs):
    infos = {}
    infos['commits_amount'] = commits_index.get_commits_amount(**query_kwargs)
    if not infos['commits_amount']:
        return infos
    first, last, duration = commits_index.get_commits_time_delta(
        **query_kwargs)
    infos['first'] = first
    infos['last'] = last
    infos['duration'] = duration
    ttl_average = commits_index.get_ttl_stats(**query_kwargs)[1]['avg']
    infos['ttl_average'] = timedelta(
        seconds=int(ttl_average)) - timedelta(seconds=0)
    infos['line_modifieds_amount'] = int(
        commits_index.get_line_modifieds_stats(**query_kwargs)[1]['sum'])
    return infos


def get_commits_histo(commits_index, query_kwargs):
    histo = commits_index.get_commits_histo(**query_kwargs)
    histo = [{'date': d['key_as_string'],
              'value': d['doc_count']} for d in histo[1]]
    return histo


def top_projects_sanitize(commits_index, projects_index,
                          query_kwargs, inc_repos_detail,
                          project_scope=None):
    projects = projects_index.get_projects()
    c_repos = commits_index.get_repos(**query_kwargs)[1]
    lm_repos = commits_index.get_top_repos_by_lines(**query_kwargs)[1]
    if project_scope:
        c_projects = [project_scope]
    else:
        c_projects = get_projects_from_references(projects, c_repos)

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
            p_filter = get_references_filter(p_repos, None)
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
