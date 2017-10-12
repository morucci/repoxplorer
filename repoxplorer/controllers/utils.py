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

import base64
import hashlib
from datetime import datetime
from datetime import timedelta
from collections import OrderedDict

from Crypto.Cipher import XOR

from pecan import conf
from pecan import abort

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
    return list(c_projects)


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
                   inc_merge_commit, metadata, exc_groups):

    projects_index._enrich_projects()

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

    mails_neg = False

    if exc_groups:
        mails_to_exclude = {}
        domains_to_exclude = []
        mails_neg = True
        groups_splitted = exc_groups.split(',')
        for gid in groups_splitted:
            _, group = idents.get_group_by_id(gid)
            mails_to_exclude.update(group['emails'])
            domains_to_exclude.extend(group.get('domains', []))

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

    if mails_neg:
        mails = mails_to_exclude
        domains = domains_to_exclude

    query_kwargs = {
        'repos': p_filter,
        'fromdate': dfrom,
        'mails': mails,
        'domains': domains,
        'mails_neg': mails_neg,
        'todate': dto,
        'merge_commit': inc_merge_commit,
        'metadata': _metadata,
    }
    return query_kwargs


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
    infos['ttl_average'] = \
        timedelta(seconds=int(ttl_average)) - timedelta(seconds=0)
    infos['ttl_average'] = int(infos['ttl_average'].total_seconds())

    infos['line_modifieds_amount'] = int(
        commits_index.get_line_modifieds_stats(**query_kwargs)[1]['sum'])
    return infos


def get_commits_histo(commits_index, query_kwargs):
    histo = commits_index.get_commits_histo(**query_kwargs)
    histo = [{'date': d['key_as_string'],
              'value': d['doc_count']} for d in histo[1]]
    return histo
