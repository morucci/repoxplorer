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


from pecan import abort
from pecan import expose
from pecan import request
from pecan import response
from pecan.rest import RestController

from repoxplorer import index
from repoxplorer.index import users

indexname = 'repoxplorer'


class UsersController(RestController):

    def _validate(self, data):
        mandatory_keys = (
            'uid', 'name', 'default-email', 'emails')
        email_keys = (
            ('email', True),
            ('groups', False))
        group_keys = (
            ('group', True),
            ('start-date', False),
            ('end-date', False))
        # All keys must be provided
        if set(data.keys()) != set(mandatory_keys):
            # Mandatory keys are missing
            return False
        if not isinstance(data['emails'], list):
            # Wrong data type for email
            return False
        mekeys = set([mk[0] for mk in email_keys if mk[1]])
        mgkeys = set([mk[0] for mk in group_keys if mk[1]])
        if data['emails']:
            for email in data['emails']:
                if not mekeys.issubset(set(email.keys())):
                    # Mandatory keys are missing
                    return False
                if not set(email.keys()).issubset(
                        set([k[0] for k in email_keys])):
                    # Found extra keys
                    return False
                if 'groups' in email.keys():
                    for group in email['groups']:
                        if not mgkeys.issubset(set(group.keys())):
                            # Mandatory keys are missing
                            return False
                        if not set(group.keys()).issubset(
                                set([k[0] for k in group_keys])):
                            # Found extra keys
                            return False
        return True

    @expose('json')
    def get(self, uid):
        _users = users.Users(
            index.Connector(index=indexname, index_suffix='users'))
        u = _users.get(uid)
        if not u:
            abort(404)
        return _users.get(uid)

    @expose('json')
    def delete(self, uid):
        _users = users.Users(
            index.Connector(index=indexname, index_suffix='users'))
        u = _users.get(uid)
        if not u:
            abort(404)
        _users.delete(uid)

    @expose('json')
    def put(self, uid):
        _users = users.Users(
            index.Connector(index=indexname, index_suffix='users'))
        u = _users.get(uid)
        if u:
            abort(409)
        infos = request.json if request.content_length else {}
        if not self._validate(infos):
            abort(400)
        # Need to check infos content
        infos['uid'] = uid
        _users.create(infos)
        response.status = 201

    @expose('json')
    def post(self, uid):
        _users = users.Users(
            index.Connector(index=indexname, index_suffix='users'))
        u = _users.get(uid)
        if not u:
            abort(404)
        infos = request.json if request.content_length else {}
        if not self._validate(infos):
            abort(400)
        # Need to check infos content
        _users.update(infos)
