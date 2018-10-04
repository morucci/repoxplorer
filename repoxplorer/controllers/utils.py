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
from datetime import datetime

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


def authors_sanitize(idents, authors):
    sanitized = {}
    _idents = idents.get_idents_by_emails(authors.keys())
    for iid, ident in _idents.items():
        sanitized[ident['default-email']] = [0, ident['name'], iid]
        for ident_email in ident['emails']:
            if ident_email in authors:
                sanitized[ident['default-email']][0] += authors[ident_email]
    return sanitized


def get_projects_from_references(pi, references):
    projects = set()
    lookup = pi.get_ref2projects_lookup()
    for ref in references:
        projects.update(lookup.get(ref, []))
    return list(projects)


def get_references_filter(project, inc_references=None):
    r_filter = {}
    can_use_meta_ref = True
    if inc_references:
        # The use of the meta ref is possible if we want stats of the complete
        # project
        can_use_meta_ref = False
    if "repos" in project:
        for r in project['repos']:
            if inc_references:
                if not "%(name)s:%(branch)s" % r in inc_references:
                    continue
            r_filter["%(uri)s:%(name)s:%(branch)s" % r] = r.get('paths')
            if r.get('paths'):
                # There is a path restriction then we cannot use the meta ref
                can_use_meta_ref = False
    if can_use_meta_ref and 'meta_ref' in project:
        r_filter = {'meta_ref: %s' % project['name']: None}
    return r_filter


def get_mail_filter(idents, cid=None, gid=None, group=None):
    if cid:
        id, ident = idents.get_ident_by_id(cid)
        if not ident:
            # No ident has been declared for that contributor
            ident = idents.get_idents_by_emails(cid).values()[0]
        return ident['emails']
    elif gid:
        if not group:
            _, group = idents.get_group_by_id(gid)
        return group['emails']
    else:
        return {}


def filters_validation(projects_index, idents, pid=None, tid=None,
                       cid=None, gid=None, dfrom=None, dto=None,
                       inc_merge_commit=None, inc_repos=None, metadata=None,
                       exc_groups=None, inc_groups=None):

    if pid and tid:
        abort(400, detail="pid and tid are exclusive")
    if cid and gid:
        abort(400, detail="cid and gid are exclusive")

    if exc_groups and inc_groups:
        abort(400, detail="exc_groups and inc_groups are exclusive")

    if (exc_groups or inc_groups) and not (pid or tid):
        abort(400, detail=(
            'exc_groups or inc_groups can only be used'
            'with pid or tid parameters'))

    if exc_groups and len(exc_groups.split(',')) > 1:
        abort(400, detail="as of now exc_groups supports only one group")
    if inc_groups and len(inc_groups.split(',')) > 1:
        abort(400, detail="as of now inc_groups supports only one group")

    if pid:
        project = projects_index.get_projects().get(pid)
        if not project:
            abort(404,
                  detail="The project has not been found")
    if tid:
        project = projects_index.get_tags().get(tid)
        if not project:
            abort(404,
                  detail="The tag has not been found")
    if cid:
        try:
            cid = decrypt(xorkey, cid)
        except Exception:
            abort(404,
                  detail="The cid is incorrectly formated")

    if gid:
        _, group = idents.get_group_by_id(gid)
        if not group:
            abort(404,
                  detail="The group has not been found")

    try:
        if dfrom:
            datetime.strptime(dfrom, "%Y-%m-%d")
        if dto:
            datetime.strptime(dto, "%Y-%m-%d")
    except Exception:
        abort(400,
              detail="Date format is expected to be 'Y-m-d'")


def resolv_filters(projects_index, idents, pid,
                   tid, cid, gid, dfrom, dto, inc_repos,
                   inc_merge_commit, metadata, exc_groups,
                   inc_groups):

    projects_index._enrich_projects()

    filters_validation(
        projects_index, idents, pid=pid, tid=tid, cid=cid, gid=gid,
        dfrom=dfrom, dto=dto, inc_merge_commit=inc_merge_commit,
        inc_repos=inc_repos, metadata=metadata, exc_groups=exc_groups,
        inc_groups=inc_groups)

    mails = {}
    domains = []

    if pid:
        project = projects_index.get_projects().get(pid)
        project['name'] = pid
        p_filter = get_references_filter(project, inc_repos)
    elif tid:
        project = projects_index.get_tags().get(tid)
        project['name'] = pid
        p_filter = get_references_filter(project, inc_repos)
    else:
        p_filter = []

    _metadata = []
    if not metadata:
        metadata = ""
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

    if exc_groups and (pid or tid):
        mails_to_exclude = {}
        domains_to_exclude = []
        mails_neg = True
        groups_splitted = exc_groups.split(',')
        for _gid in groups_splitted:
            _, group = idents.get_group_by_id(_gid)
            mails_to_exclude.update(group['emails'])
            domains_to_exclude.extend(group.get('domains', []))

    if inc_groups and (pid or tid):
        groups_splitted = inc_groups.split(',')
        for _gid in groups_splitted:
            _, group = idents.get_group_by_id(_gid)
            mails.update(group['emails'])
            domains.extend(group.get('domains', []))

    if cid or gid:
        if cid:
            cid = decrypt(xorkey, cid)
            mails = get_mail_filter(idents, cid=cid)
        if gid:
            _, group = idents.get_group_by_id(gid)
            mails = get_mail_filter(idents, gid=gid, group=group)
            domains.extend(group.get('domains', []))

    if dfrom:
        dfrom = datetime.strptime(dfrom, "%Y-%m-%d").strftime('%s')

    if dto:
        dto = str(
            int(datetime.strptime(dto, "%Y-%m-%d").strftime('%s')) + 24 * 3600)

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
