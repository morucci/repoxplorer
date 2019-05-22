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


from pecan import conf
from pecan import abort
from pecan import expose
from pecan import request
from pecan import response
from pecan.rest import RestController

from repoxplorer import index
from repoxplorer.exceptions import UnauthorizedException
from repoxplorer.index import users
from repoxplorer.controllers import utils

if conf.get('users_endpoint', False) and conf.get('oidc', False):
    from repoxplorer.auth import OpenIDConnectEngine as AuthEngine
else:
    from repoxplorer.auth import CAuthEngine as AuthEngine


AUTH_ENGINE = AuthEngine()
xorkey = conf.get('xorkey') or 'default'


class UsersController(RestController):

    auth = AUTH_ENGINE

    def abort_if_not_active(self):
        if not self.auth.is_configured():
            abort(403)

    def _authorize(self, uid=None):
        self.abort_if_not_active()
        # Shortcircuit the authorization for testing purpose
        # return
        try:
            self.auth.authorize(request, uid)
        except UnauthorizedException:
            abort(401)
        except Exception as e:
            abort(500, "Unexpected error: %s" % e)
        self.auth.provision_user(request)

    def _validate(self, data):
        mandatory_keys = (
            'uid', 'name', 'default-email', 'emails')
        email_keys = (
            ('email', True),
            ('groups', False))
        group_keys = (
            ('group', True),
            ('begin-date', False),
            ('end-date', False))
        # All keys must be provided
        if set(data.keys()) != set(mandatory_keys):
            # Mandatory keys are missing
            return False
        if not isinstance(data['emails'], list):
            # Wrong data type for email
            return False
        if len(data['name']) >= 100:
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

    def _modify_protected_fields(self, prev, new):
        if new['uid'] != prev['uid']:
            return True
        if new['default-email'] != prev['default-email']:
            return True
        # Adding or removing emails is forbidden
        prev_emails = set([e['email'] for e in prev['emails']])
        new_emails = set([e['email'] for e in new['emails']])
        if (not new_emails.issubset(prev_emails) or
                not prev_emails.issubset(new_emails)):
            return True
        return False

    # curl -H 'Remote-User: admin' -H 'Admin-Token: abc' \
    # "http://localhost:51000/api/v1/users/fabien"
    @expose('json')
    def get(self, uid):
        self._authorize(uid)
        _users = users.Users(
            index.Connector(index_suffix='users'))
        u = _users.get(uid)
        if not u:
            abort(404)
        u['cid'] = utils.encrypt(xorkey, u['default-email'])
        return u

    @expose('json')
    def delete(self, uid):
        self._authorize(uid)
        _users = users.Users(
            index.Connector(index_suffix='users'))
        u = _users.get(uid)
        if not u:
            abort(404)
        _users.delete(uid)

    # curl -X PUT -H 'Remote-User: admin' -H 'Admin-Token: abc' \
    # -H "Content-Type: application/json" --data \
    # '{"uid":"fabien","name":"Fabien Boucher","default-email": \
    # "fboucher@redhat.com","emails": [{"email": "fboucher@redhat.com"}]}' \
    # "http://localhost:51000/api/v1/users/fabien"
    @expose('json')
    def put(self, uid):
        # We don't pass uid to authorize, then only admin logged with
        # admin token will be authorized
        self._authorize()
        _users = users.Users(
            index.Connector(index_suffix='users'))
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

    # curl -X POST -H 'Remote-User: admin' -H 'Admin-Token: abc' \
    # -H "Content-Type: application/json" --data \
    # '{"uid":"fabien","name":"Fabien Boucher","default-email": \
    # "fboucher@redhat.com","emails": [{"email": "fboucher@redhat.com"}, \
    # {"email": "fabien.boucher@enovance.com"}]}' \
    # "http://localhost:51000/api/v1/users/fabien"
    @expose('json')
    def post(self, uid):
        requester = self._authorize(uid)
        _users = users.Users(
            index.Connector(index_suffix='users'))
        u = _users.get(uid)
        if not u:
            abort(404)
        infos = request.json if request.content_length else {}
        infos['uid'] = uid
        # Can be provided by mistake, just remove it
        if 'cid' in infos:
            del infos['cid']
        if not self._validate(infos):
            abort(400)
        if requester != 'admin':
            # User is not allowed to modify some raw_fields
            # like adding or removing emails ...
            if self._modify_protected_fields(u, infos):
                abort(403)
        _users.update(infos)
