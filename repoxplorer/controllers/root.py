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


import hashlib
import itertools

from pecan import expose
from pecan import abort
from pecan import conf

from datetime import datetime
from collections import OrderedDict

from repoxplorer.controllers import utils
from repoxplorer.controllers import groups
from repoxplorer.controllers import users
from repoxplorer.controllers import histo
from repoxplorer.controllers import infos
from repoxplorer import index
from repoxplorer import version
from repoxplorer.index.commits import Commits
from repoxplorer.index.commits import PROPERTIES
from repoxplorer.index.projects import Projects
from repoxplorer.index.contributors import Contributors
from repoxplorer.index.tags import Tags


indexname = 'repoxplorer'
xorkey = conf.get('xorkey') or 'default'
rx_version = version.get_version()
index_custom_html = conf.get('index_custom_html', '')


class V1Controller(object):

    infos = infos.InfosController()
    groups = groups.GroupsController()
    users = users.UsersController()
    histo = histo.HistoController()

    @expose('json')
    def version(self):
        return {'version': rx_version}

    @expose('json')
    def status(self):
        projects_index = Projects()
        projects = projects_index.get_projects()
        num_projects = len(projects)
        num_repos = len(set([
            ref['name'] for
            ref in itertools.chain(
                *[p['repos'] for p in projects.values()])]))
        return {'customtext': index_custom_html,
                'projects': num_projects,
                'repos': num_repos,
                'version': rx_version}

    @expose('json')
    def projects(self):
        projects_index = Projects()
        projects = projects_index.get_projects()
        projects = OrderedDict(
            sorted(projects.items(), key=lambda t: t[0]))
        tags = projects_index.get_tags()
        return {'projects': projects,
                'tags': tags.keys()}

    @expose('json')
    def search_authors(self, query=""):
        c = Commits(index.Connector(index=indexname))
        ret = c.es.search(
            index=c.index, doc_type=c.dbname,
            q=query, df="author_name", size=10000,
            default_operator="AND",
            _source_include=["author_name", "author_email"])
        ret = ret['hits']['hits']
        if not len(ret):
            return {}
        idents = Contributors()
        ret = dict([(d['_source']['author_email'],
                     d['_source']['author_name']) for d in ret])
        return utils.search_authors_sanitize(idents, ret)

    @expose('json')
    def metadata(self, key=None, pid=None, tid=None, cid=None, gid=None,
                 dfrom=None, dto=None, inc_merge_commit=None,
                 inc_repos=None, exc_groups=None):
        c = Commits(index.Connector(index=indexname))
        projects_index = Projects()
        idents = Contributors()

        query_kwargs = utils.resolv_filters(
            projects_index, idents, pid, tid, cid, gid,
            dfrom, dto, inc_repos, inc_merge_commit, "", exc_groups)
        del query_kwargs['metadata']

        if not key:
            keys = c.get_metadata_keys(**query_kwargs)
            return keys
        else:
            vals = c.get_metadata_key_values(key, **query_kwargs)
            return vals

    @expose('json')
    def tags(self, pid=None, tid=None,
             dfrom=None, dto=None, inc_repos=None):
        t = Tags(index.Connector(index=indexname))
        projects_index = Projects()

        query_kwargs = utils.resolv_filters(
            projects_index, None, pid, tid, None, None,
            dfrom, dto, inc_repos, None, "", None)

        p_filter = [":".join(r.split(':')[:-1]) for r in query_kwargs['repos']]
        ret = [r['_source'] for r in t.get_tags(p_filter, dfrom, dto)]
        # TODO: if tid is given we can include user defined releases
        # for repo tagged with tid.
        if not pid:
            return ret
        # now append user defined releases
        ur = {}
        project = projects_index.get_projects()[pid]
        for repo in project['repos']:
            if 'releases' in repo:
                for release in repo['releases']:
                    ur[release['name']] = {'name': release['name'],
                                           'date': release['date'],
                                           'repo': repo['name']}
        for rel in ur.values():
            ret.append(rel)
        return ret

    @expose('json')
    def commits(self, pid=None, tid=None, cid=None, gid=None,
                start=0, limit=10,
                dfrom=None, dto=None, inc_merge_commit=None,
                inc_repos=None, metadata="", exc_groups=None):

        c = Commits(index.Connector(index=indexname))
        projects_index = Projects()
        idents = Contributors()

        query_kwargs = utils.resolv_filters(
            projects_index, idents, pid, tid, cid, gid,
            dfrom, dto, inc_repos, inc_merge_commit,
            metadata, exc_groups)
        query_kwargs.update(
            {'start': start, 'limit': limit})

        resp = c.get_commits(**query_kwargs)

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


class APIController(object):

    v1 = V1Controller()


class RootController(object):

    api = APIController()

# The use of templates for pages will be replaced soon
# Pages will be rederred by JS only. Today rendering
# is a mixed of Mako templating and JS

    @expose(template='index.html')
    def index(self):
        return self.api.v1.status()

    @expose(template='groups.html')
    def groups(self):
        return {'version': rx_version}

    @expose(template='projects.html')
    def projects(self):
        ret = self.api.v1.projects()
        ret.update({'version': rx_version})
        return ret

    @expose(template='contributors.html')
    def contributors(self):
        return {'version': rx_version}

    @expose(template='contributor.html')
    def contributor(self, cid, pid=None,
                    dfrom=None, dto=None,
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
                dfrom, "%Y-%m-%d").strftime('%s')
        if dto:
            dto = datetime.strptime(
                dto, "%Y-%m-%d").strftime('%s')
        c = Commits(index.Connector(index=indexname))
        idents = Contributors()
        projects = Projects()
        iid, ident = idents.get_ident_by_id(cid)
        if not ident:
            # No ident has been declared for that contributor
            iid, ident = idents.get_ident_by_email(cid)
        mails = ident['emails']
        name = ident['name']
        if not name:
            if not name:
                raw_names = c.get_commits_author_name_by_emails([cid])
                if cid not in raw_names:
                    # TODO: get_commits_author_name_by_emails must
                    # support look by committer email too
                    name = 'Unamed'
                else:
                    name = raw_names[cid]

            name = raw_names[cid]

        p_filter = {}
        if pid:
            projects_index = Projects()
            repos = projects_index.get_projects()[pid]
            p_filter = utils.get_references_filter(repos)

        query_kwargs = {
            'fromdate': dfrom,
            'todate': dto,
            'mails': mails,
            'merge_commit': include_merge_commit,
            'repos': p_filter,
        }

        if dfrom is None or dto is None:
            period = (None, None)
        else:
            period = (datetime.fromtimestamp(float(dfrom)),
                      datetime.fromtimestamp(float(dto)))

        infos = utils.get_generic_infos(c, query_kwargs)

        if not infos['commits_amount']:
            # No commit found
            return {'name': name,
                    'gravatar': hashlib.md5(
                        ident['default-email']).hexdigest(),
                    'cid': utils.encrypt(xorkey, cid),
                    'period': period,
                    'empty': True,
                    'version': rx_version}

        top_projects = utils.top_projects_sanitize(
            c, projects, query_kwargs, inc_repos_detail)

        sorted_repos_contributed = top_projects[0]
        sorted_repos_contributed_modified = top_projects[1]
        c_projects = top_projects[2]
        c_repos = top_projects[3]

        return {'name': name,
                'gravatar': hashlib.md5(ident['default-email']).hexdigest(),
                'commits_amount': infos['commits_amount'],
                'line_modifieds_amount': infos['line_modifieds_amount'],
                'period': period,
                'repos': sorted_repos_contributed,
                'repos_line_mdfds': sorted_repos_contributed_modified,
                'projects_amount': len(c_projects),
                'repos_amount': len(c_repos),
                'known_emails_amount': len(mails),
                'first': datetime.fromtimestamp(infos['first']),
                'last': datetime.fromtimestamp(infos['last']),
                'duration': (datetime.fromtimestamp(infos['duration']) -
                             datetime.fromtimestamp(0)),
                'ttl_average': infos['ttl_average'],
                'cid': utils.encrypt(xorkey, cid),
                'empty': False,
                'inc_repos_detail': inc_repos_detail,
                'version': rx_version}

    @expose(template='group.html')
    def group(self, gid, pid=None, dfrom=None, dto=None,
              inc_merge_commit=None,
              inc_repos_detail=None):
        if inc_merge_commit != 'on':
            include_merge_commit = False
        else:
            # The None value will return all whatever
            # the commit is a merge one or not
            include_merge_commit = None
        if dfrom:
            dfrom = datetime.strptime(
                dfrom, "%Y-%m-%d").strftime('%s')
        if dto:
            dto = datetime.strptime(
                dto, "%Y-%m-%d").strftime('%s')
        c = Commits(index.Connector(index=indexname))
        idents = Contributors()
        projects = Projects()
        gid, group = idents.get_group_by_id(gid)
        if not group:
            abort(404,
                  detail="The group has not been found")
        mails = group['emails']
        domains = group.get('domains', [])
        description = group['description']
        members = {}
        for email in mails:
            iid, ident = idents.get_ident_by_email(email)
            members[iid] = ident

        p_filter = {}
        if pid:
            projects_index = Projects()
            repos = projects_index.get_projects()[pid]
            p_filter = utils.get_references_filter(repos)

        query_kwargs = {
            'fromdate': dfrom,
            'todate': dto,
            'mails': mails,
            'domains': domains,
            'merge_commit': include_merge_commit,
            'repos': p_filter,
        }

        if dfrom is None or dto is None:
            period = (None, None)
        else:
            period = (datetime.fromtimestamp(float(dfrom)),
                      datetime.fromtimestamp(float(dto)))

        infos = utils.get_generic_infos(c, query_kwargs)

        if not infos['commits_amount']:
            # No commit found
            return {'name': gid,
                    'description': description,
                    'gid': gid,
                    'period': period,
                    'empty': True,
                    'version': rx_version}

        top_projects = utils.top_projects_sanitize(
            c, projects, query_kwargs, inc_repos_detail, pid)

        sorted_repos_contributed = top_projects[0]
        sorted_repos_contributed_modified = top_projects[1]
        c_projects = top_projects[2]
        c_repos = top_projects[3]

        top_authors = c.get_authors(**query_kwargs)
        top_authors_modified = c.get_top_authors_by_lines(**query_kwargs)

        idents = Contributors()
        top_authors = utils.top_authors_sanitize(
            idents, top_authors, c, top=25)
        top_authors_modified = utils.top_authors_sanitize(
            idents, top_authors_modified, c, top=25)

        return {'name': gid,
                'description': description,
                'members_amount': len(members.keys()),
                'commits_amount': infos['commits_amount'],
                'top_authors': top_authors,
                'top_authors_modified': top_authors_modified,
                'line_modifieds_amount': infos['line_modifieds_amount'],
                'period': period,
                'repos': sorted_repos_contributed,
                'repos_line_mdfds': sorted_repos_contributed_modified,
                'projects_amount': len(c_projects),
                'repos_amount': len(c_repos),
                'known_emails_amount': len(mails),
                'first': datetime.fromtimestamp(infos['first']),
                'last': datetime.fromtimestamp(infos['last']),
                'duration': (datetime.fromtimestamp(infos['duration']) -
                             datetime.fromtimestamp(0)),
                'ttl_average': infos['ttl_average'],
                'inc_repos_detail': inc_repos_detail,
                'gid': gid,
                'empty': False,
                'version': rx_version}

    @expose(template='project.html')
    def project(self, pid=None, tid=None, dfrom=None, dto=None,
                inc_merge_commit=None, inc_repos=None, metadata=None,
                exc_groups=None):
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
            dfrom = datetime.strptime(dfrom, "%Y-%m-%d").strftime('%s')
        if dto:
            dto = datetime.strptime(dto, "%Y-%m-%d").strftime('%s')
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

        mails_to_exclude = {}
        domains_to_exclude = []
        if exc_groups:
            groups_splitted = exc_groups.split(',')
            idents = Contributors()
            for gid in groups_splitted:
                _, group = idents.get_group_by_id(gid)
                mails_to_exclude.update(group['emails'])
                domains_to_exclude.extend(group.get('domains', []))

        projects_index = Projects()
        if pid:
            repos = projects_index.get_projects()[pid]
        else:
            repos = projects_index.get_tags()[tid]

        p_filter = utils.get_references_filter(repos, inc_repos)

        query_kwargs = {
            'repos': p_filter,
            'fromdate': dfrom,
            'mails': mails_to_exclude,
            'domains': domains_to_exclude,
            'mails_neg': True,
            'todate': dto,
            'merge_commit': include_merge_commit,
            'metadata': metadata,
        }

        if dfrom is None or dto is None:
            period = (None, None)
        else:
            period = (datetime.fromtimestamp(float(dfrom)),
                      datetime.fromtimestamp(float(dto)))

        c = Commits(index.Connector(index=indexname))

        infos = utils.get_generic_infos(c, query_kwargs)

        if not infos['commits_amount']:
            # No commit found
            return {'pid': pid,
                    'tid': tid,
                    'period': period,
                    'repos': repos['repos'],
                    'inc_repos': inc_repos,
                    'empty': True,
                    'version': True}

        top_authors = c.get_authors(**query_kwargs)
        top_authors_modified = c.get_top_authors_by_lines(**query_kwargs)

        authors_amount = len(top_authors[1])

        idents = Contributors()
        top_authors = utils.top_authors_sanitize(
            idents, top_authors, c, top=25)
        top_authors_modified = utils.top_authors_sanitize(
            idents, top_authors_modified, c, top=25)

        return {'pid': pid,
                'tid': tid,
                'top_authors': top_authors,
                'top_authors_modified': top_authors_modified,
                'authors_amount': authors_amount,
                'commits_amount': infos['commits_amount'],
                'repos': repos['repos'],
                'inc_repos': inc_repos,
                'period': period,
                'first': datetime.fromtimestamp(infos['first']),
                'last': datetime.fromtimestamp(infos['last']),
                'duration': (datetime.fromtimestamp(infos['duration']) -
                             datetime.fromtimestamp(0)),
                'ttl_average': infos['ttl_average'],
                'empty': False,
                'version': rx_version}
