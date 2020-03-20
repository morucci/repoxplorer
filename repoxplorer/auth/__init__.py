# Copyright 2019, Matthieu Huin
# Copyright 2019, Red Hat
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

"""Various authentication engines supported by RepoXplorer."""

import base64
import json
import jwt
from urllib.parse import urljoin
import requests

from pecan import conf

from repoxplorer.exceptions import UnauthorizedException
from repoxplorer import index
from repoxplorer.index import users


class BaseAuthEngine(object):
    """The base auth engine class."""

    def is_configured(self) -> bool:
        """Activate the users REST endpoint if authentication is configured."""
        return False

    def authorize(self, request, uid=None) -> str:
        """Make sure the authenticated user is allowed an action."""
        raise UnauthorizedException("Not implemented")

    def provision_user(self, request) -> None:
        """If needed, the user can be provisioned based on the user info passed
        by the Identity Provider."""
        return


class CAuthEngine(BaseAuthEngine):
    """Cauth relies on Apache + mod_auth_authtkt to set a Remote-User header.
    User provisioning is done out of the band by Cauth itself, calling the
    PUT endpoint on the users API."""

    def is_configured(self):
        return conf.get('users_endpoint', False)

    def authorize(self, request, uid=None):
        """Make sure the request is authorized.
        Returns the authorized user's uid or raises if unauthorized."""
        if not request.remote_user:
            request.remote_user = request.headers.get('Remote-User')
        if not request.remote_user:
            request.remote_user = request.headers.get('X-Remote-User')
        if request.remote_user == '(null)':
            if request.headers.get('Authorization'):
                auth_header = request.headers.get('Authorization').split()[1]
                request.remote_user = base64.b64decode(
                    auth_header).split(':')[0]
        if (request.remote_user == "admin" and
                request.headers.get('Admin-Token')):
            sent_admin_token = request.headers.get('Admin-Token')
            # If remote-user is admin and an admin-token is passed
            # authorized if the token is correct
            if sent_admin_token == conf.get('admin_token'):
                return 'admin'
        else:
            # If uid targeted by the request is the same
            # as the requester then authorize
            if uid and uid == request.remote_user:
                return uid
            if uid and uid != request.remote_user:
                raise UnauthorizedException("Admin action only")
        raise UnauthorizedException("unauthorized")


class OpenIDConnectEngine(BaseAuthEngine):
    """Expects a Bearer token sent through the 'Authorization' header.
    The token is verified against a JWK, pulled from the well-known
    configuration of the OIDC provider.

    The claims will be used to provision users if authorization is
    successful."""

    config = conf.get('oidc', {})

    def is_configured(self):
        return self.config.get('issuer_url', False)

    def _get_issuer_info(self):
        issuer_url = self.config.get('issuer_url')
        verify_ssl = self.config.get('verify_ssl', True)
        issuer_info = requests.get(
            urljoin(issuer_url, '.well-known/openid-configuration'),
            verify=verify_ssl)
        if issuer_info.status_code > 399:
            raise UnauthorizedException(
                "Cannot fetch OpenID provider's configuration")
        return issuer_info.json()

    def _get_signing_key(self, jwks_uri, key_id):
        verify_ssl = self.config.get('verify_ssl', True)
        certs = requests.get(jwks_uri, verify=verify_ssl)
        if certs.status_code > 399:
            raise UnauthorizedException("Cannot fetch JWKS")
        for k in certs.json()['keys']:
            if k['kid'] == key_id:
                return (jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(k)),
                        k['alg'])
        raise UnauthorizedException("Key %s not found" % key_id)

    def _get_raw_token(self, request):
        if request.headers.get('Authorization', None) is None:
            raise UnauthorizedException('Missing "Authorization" header')
        auth_header = request.headers.get('Authorization', None)
        if not auth_header.lower().startswith('bearer '):
            raise UnauthorizedException('Invalid "Authorization" header')
        token = auth_header[len('bearer '):]
        return token

    def authorize(self, request, uid=None):
        token = self._get_raw_token(request)
        issuer_info = self._get_issuer_info()
        unverified_headers = jwt.get_unverified_header(token)
        key_id = unverified_headers.get('kid', None)
        if key_id is None:
            raise UnauthorizedException("Missing key id in token")
        jwks_uri = issuer_info.get('jwks_uri')
        if jwks_uri is None:
            raise UnauthorizedException("Missing JWKS URI in config")
        key, algo = self._get_signing_key(jwks_uri, key_id)
        try:
            claims = jwt.decode(token, key, algorithms=algo,
                                issuer=issuer_info['issuer'],
                                audience=self.config['audience'])
        except Exception as e:
            raise UnauthorizedException('Invalid access token: %s' % e)
        if claims['preferred_username'] == self.config.get('admin_username',
                                                           'admin'):
            return 'admin'
        if uid and uid == claims['preferred_username']:
            return uid
        if uid and uid != claims['preferred_username']:
            raise UnauthorizedException("Only the admin ")
        raise UnauthorizedException('unauthorized')

    def provision_user(self, request):
        raw_token = self._get_raw_token(request)
        # verified before so it's totally okay
        claims = jwt.decode(raw_token, verify=False)
        # TODO assuming the presence of claims, but a specific scope might be
        # needed.
        # These are expected to be standard though, see
        # https://openid.net/specs/openid-connect-core-1_0.html#StandardClaims
        email = claims['email']
        uid = claims['preferred_username']
        name = claims['name']
        _users = users.Users(index.Connector(index_suffix='users'))
        u = _users.get(uid)
        infos = {'uid': uid,
                 'name': name,
                 'default-email': email,
                 'emails': [{'email': email}]}
        if u:
            _users.update(infos)
        else:
            _users.create(infos)
