# Copyright 2017, Red Hat
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
from pecan import expose
from datetime import datetime

from Crypto.Cipher import XOR

from repoxplorer import index
from repoxplorer.index.commits import Commits
from repoxplorer.index.commits import PROPERTIES
from repoxplorer.index.projects import Projects
from repoxplorer.index.contributors import Contributors

indexname = 'repoxplorer'
xorkey = 'default'


def encrypt(key, plaintext):
    cipher = XOR.new(key)
    return base64.b64encode(cipher.encrypt(plaintext))


def decrypt(self, key, ciphertext):
    cipher = XOR.new(key)
    return cipher.decrypt(base64.b64decode(ciphertext))


def get_repos_filter(repos, inc_repos):
    p_filter = []
    for p in repos:
        if inc_repos:
            if not "%s:%s" % (p['name'], p['branch']) in inc_repos:
                continue
        p_filter.append("%s:%s:%s" % (p['uri'],
                                      p['name'],
                                      p['branch']))
    return p_filter


def get_mail_filter(idents, cid):
    if cid in idents:
        return idents[cid][2]
    else:
        return [cid]


def resolv_filters(projects_index, idents, pid,
                   tid, cid, dfrom, dto, inc_repos,
                   inc_merge_commit):

    if pid:
        project = projects_index.get_projects()[pid]
        p_filter = get_repos_filter(project, inc_repos)
    elif tid:
        project = Projects().get_repos_by_tag(tid)
        p_filter = get_repos_filter(project, inc_repos)
    else:
        p_filter = []

    if cid:
        cid = decrypt(xorkey, cid)
        mails = get_mail_filter(idents, cid)
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
def commits(pid=None, tid=None, cid=None, start=0, limit=10,
            dfrom=None, dto=None, inc_merge_commit=None,
            inc_repos=None, metadata=""):
    print "AA"
    print pid
    print tid
    c = Commits(index.Connector(index=indexname))
    projects_index = Projects()
    idents = Contributors().get_contributors()
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

    p_filter, mails, dfrom, dto, inc_merge_commit = resolv_filters(
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
        # Add cid and ccid
        cmt['cid'] = encrypt(xorkey, cmt['author_email'])
        cmt['ccid'] = encrypt(xorkey, cmt['committer_email'])
        # Remove email details
        del cmt['author_email']
        del cmt['committer_email']
    return resp
