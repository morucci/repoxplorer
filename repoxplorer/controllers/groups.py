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
import hashlib

from pecan import conf
from pecan import expose

from repoxplorer import index
from repoxplorer.controllers import utils
from repoxplorer.index.contributors import Contributors
from repoxplorer.index.commits import Commits

indexname = 'repoxplorer'
xorkey = conf.get('xorkey') or 'default'


class GroupsController(object):

    @expose('json')
    def index(self, prefix=None, nameonly='false'):
        ci = Commits(index.Connector(index=indexname))
        contributors_index = Contributors()
        groups = contributors_index.get_groups()
        if nameonly == 'true':
            ret = dict([(k, None) for k in groups.keys()])
            if prefix:
                ret = dict([(k, None) for k in ret.keys() if
                            k.lower().startswith(prefix)])
            return ret
        ret_groups = {}
        for group, data in groups.items():
            if prefix and not group.lower().startswith(prefix):
                continue
            rg = {'members': {}, 'description': data['description']}
            for email, bounces in data['emails'].items():
                id, member = contributors_index.get_ident_by_email(email)
                member = copy.deepcopy(member)
                member['gravatar'] = hashlib.md5(
                    member['default-email']).hexdigest()
                member['bounces'] = bounces
                del member['emails']
                if not member['name']:
                    # Try to find it among commits
                    suggested = ci.get_commits_author_name_by_emails(
                        [member['default-email']])
                    name = suggested.get(member['default-email'],
                                         'Unknown name')
                    member['name'] = name
                del member['default-email']
                rg['members'][utils.encrypt(xorkey, id)] = member
            ret_groups[group] = rg
        return ret_groups
