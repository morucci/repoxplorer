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
from Crypto.Cipher import XOR
from pecan import conf
from datetime import datetime

xorkey = conf.get('xorkey') or 'default'


def encrypt(key, plaintext):
    cipher = XOR.new(key)
    return base64.b64encode(cipher.encrypt(plaintext))


def decrypt(key, ciphertext):
    cipher = XOR.new(key)
    return cipher.decrypt(base64.b64decode(ciphertext))


def get_projects_from_references(projects, c_references):
    c_projects = set()
    for pname, references in projects.items():
        for r in references:
            rid = "%s:%s:%s" % (r['uri'],
                                r['name'],
                                r['branch'])
            if rid in c_references:
                c_projects.add(pname)
    return c_projects


def get_references_filter(references, inc_references=None):
    r_filter = []
    for r in references:
        if inc_references:
            if not "%(name)s:%(branch)s" % r in inc_references:
                continue
        r_filter.append("%(uri)s:%(name)s:%(branch)s" % r)
    return r_filter


def get_mail_filter(idents, cid):
    ident = idents.get_ident_by_id(cid)
    if not ident[1]:
        # No ident has been declared for that contributor
        ident = idents.get_ident_by_email(cid)
    return ident[1]['emails'].keys()


def resolv_filters(projects_index, idents, pid,
                   tid, cid, dfrom, dto, inc_repos,
                   inc_merge_commit):

    if pid:
        project = projects_index.get_projects()[pid]
        p_filter = get_references_filter(project, inc_repos)
    elif tid:
        project = projects_index.get_repos_by_tag(tid)
        p_filter = get_references_filter(project, inc_repos)
    else:
        p_filter = []

    if cid:
        cid = decrypt(xorkey, cid)
        mails = get_mail_filter(idents, cid)
    else:
        mails = []

    if dfrom:
        dfrom = datetime.strptime(dfrom, "%m/%d/%Y").strftime('%s')

    if dto:
        dto = datetime.strptime(dto, "%m/%d/%Y").strftime('%s')

    if inc_merge_commit == 'on':
        # The None value will return all whatever
        # the commit is a merge one or not
        inc_merge_commit = None
    else:
        inc_merge_commit = False

    return p_filter, mails, dfrom, dto, inc_merge_commit


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
