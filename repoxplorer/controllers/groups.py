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

from pecan import conf
from pecan import expose

from repoxplorer import index
from repoxplorer.controllers import utils
from repoxplorer.index.contributors import Contributors
from repoxplorer.index.commits import Commits
from repoxplorer.index.projects import Projects

xorkey = conf.get('xorkey') or 'default'


class GroupsController(object):

    @expose('json')
    def index(self, prefix=None, nameonly='false', withstats='false',
              pid=None, dfrom=None, dto=None, inc_merge_commit=None):
        ci = Commits(index.Connector())
        contributors_index = Contributors()
        groups = contributors_index.get_groups()
        if withstats == 'true':
            projects_index = Projects()
        if nameonly == 'true':
            ret = dict([(k, None) for k in groups.keys()])
            if prefix:
                ret = dict([(k, None) for k in ret.keys() if
                            k.lower().startswith(prefix)])
            return ret
        ret_groups = {}
        for group, data in groups.items():
            if prefix and not group.lower().startswith(prefix.lower()):
                continue
            rg = {'members': {},
                  'description': data['description'],
                  'domains': data.get('domains', [])}
            emails = data['emails'].keys()
            members = contributors_index.get_idents_by_emails(emails)
            for id, member in members.items():
                member['gravatar'] = hashlib.md5(
                    member['default-email']).hexdigest()
                # TODO(fbo): bounces should be a list of bounce
                # Let's deactivate that for now
                # member['bounces'] = bounces
                del member['emails']
                if not member['name']:
                    # Try to find it among commits
                    suggested = ci.get_commits_author_name_by_emails(
                        [member['default-email']])
                    name = suggested.get(member['default-email'],
                                         'Unnamed')
                    member['name'] = name
                del member['default-email']
                rg['members'][utils.encrypt(xorkey, id)] = member

            if withstats == 'true':
                # Fetch the number of projects and repos contributed to
                query_kwargs = utils.resolv_filters(
                    projects_index, contributors_index, pid, None, None, group,
                    dfrom, dto, None, inc_merge_commit, None, None, None)

                repos = filter(lambda r: not r.startswith('meta_ref: '),
                               ci.get_repos(**query_kwargs)[1])
                projects = utils.get_projects_from_references(
                    projects_index, repos)
                rg['repos_amount'] = len(repos)
                rg['projects_amount'] = len(projects)

            ret_groups[group] = rg

        return ret_groups
