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

import csv
import copy
import json
import os
import shutil
import tempfile
from datetime import datetime, timedelta
import jwt

from repoxplorer import index
from repoxplorer.tests import FunctionalTest
from repoxplorer.index.commits import Commits
from repoxplorer.index.projects import Projects
from repoxplorer.index.tags import Tags

from repoxplorer import version
from repoxplorer.controllers import root
from repoxplorer.controllers import utils

from mock import patch, MagicMock

from io import StringIO

from pecan import conf
from pecan.testing import load_test_app

xorkey = conf.get('xorkey') or 'default'

COMMITS = [
    {
        'sha': '3597334f2cb10772950c97ddf2f6cc17b183',
        'author_date': 1393860653,
        'committer_date': 1393860653,
        'ttl': 0,
        'author_name': 'Jean Paul',
        'committer_name': 'Jean Paul',
        'author_email': 'j.paul@joker.org',
        'committer_email': 'j.paul@joker.org',
        'repos': [
            'https://github.com/nakata/monkey.git:monkey:master',
            'meta_ref: test'],
        'line_modifieds': 8,
        'merge_commit': False,
        'commit_msg': 'Test commit',
        'implement': ['feature 1', ],
    },
    {
        'sha': '3597334f2cb10772950c97ddf2f6cc17b184',
        'author_date': 1410456005,
        'committer_date': 1410456005,
        'ttl': 0,
        'author_name': 'Nakata Daisuke',
        'committer_name': 'Nakata Daisuke',
        'author_email': 'n.suke@joker.org',
        'committer_email': 'n.suke@joker.org',
        'repos': [
            'https://github.com/nakata/monkey.git:monkey:master',
            'meta_ref: test'],
        'line_modifieds': 10,
        'merge_commit': False,
        'commit_msg': 'Add init method',
        'implement': ['feature 35', ],
    },
    {
        'sha': '3597334f2cb10772950c97ddf2f6cc17b1845',
        'author_date': 1410456005,
        'committer_date': 1410456005,
        'ttl': 0,
        'author_name': 'Jean Paul',
        'committer_name': 'Jean Paul',
        'author_email': 'j.paul@joker.org',
        'committer_email': 'j.paul@joker.org',
        'repos': [
            'https://github.com/nakata/monkey.git:monkey:master', ],
        'line_modifieds': 11,
        'merge_commit': False,
        'commit_msg': 'Add feature 36',
        'implement': ['feature 36', ],
        'close-bug': ['18', ],
    },
    {
        'sha': '3597334f2cb10772950c97ddf2f6cc17b1846',
        'author_date': 1410456005,
        'committer_date': 1410456005,
        'ttl': 0,
        'author_name': 'Jean Paul',
        'committer_name': 'Jean Paul',
        'author_email': 'j.paul@joker.org',
        'committer_email': 'j.paul@joker.org',
        'repos': [
            'https://github.com/nakata/monkey.git:monkey:master',
            'meta_ref: test'],
        'line_modifieds': 0,
        'merge_commit': True,
        'commit_msg': 'Merge: something',
    }]


GROUPS = {
    "grp1": {
        "description": "The group 1",
        "emails": {
            "j.paul@joker.org": {},
            }
        },
    "grp2": {
        "description": "The group 2",
        "emails": {
            "n.suke@joker.org": {},
            }
        }
    }


def build_dict_from_csv(body):
    if not isinstance(body, str):
        body = body.decode(errors='ignore')
    buf = StringIO(body)
    raw_fields = buf.readlines()[0]
    fields = raw_fields.strip().split(',')
    buf.seek(len(raw_fields))
    r = csv.DictReader(buf, fields)
    ret = []
    for row in r:
        ret.append(row)
    return ret


def set_projects_definition(con, projects_file=None):
    default_projects_file = """
    project-templates:
      default:
        uri: https://github.com/nakata/%(name)s.git
        branches:
        - master

    projects:
      test:
        repos:
          monkey:
            template: default
    """
    projects_file = projects_file or default_projects_file
    db = tempfile.mkdtemp()
    open(os.path.join(db, 'projects.yaml'), 'w+').write(projects_file)
    index.conf['db_path'] = db
    index.conf['db_default_file'] = None
    Projects(db_path=db, con=con, dump_yaml_in_index=True)
    return db


class TestErrorController(FunctionalTest):

    @classmethod
    def setUpClass(cls):
        cls.con = index.Connector(index='repoxplorertest')
        cls.conp = index.Connector(
            index='repoxplorertest', index_suffix='projects')
        c = Commits(cls.con)
        c.add_commits(COMMITS)
        cls.db = set_projects_definition(cls.conp)

    @classmethod
    def tearDownClass(cls):
        cls.con.ic.delete(index=cls.con.index)
        cls.conp.ic.delete(index=cls.conp.index)
        if os.path.isdir(cls.db):
            shutil.rmtree(cls.db)

    def test_api_infos_pid_not_found(self):
        headers = {'Accept': 'application/json'}
        response = self.app.get(
            '/api/v1/infos/infos?pid=notexists',
            headers=headers, status='*')
        self.assertEqual(response.status_int, 404)
        self.assertEqual(
            response.json['description'],
            'The project has not been found')

    def test_api_project_repos_pid_not_found(self):
        headers = {'Accept': 'application/json'}
        response = self.app.get(
            '/api/v1/projects/repos?pid=notexists',
            headers=headers, status='*')
        self.assertEqual(response.status_int, 404)
        self.assertEqual(
            response.json['description'],
            'Project ID or Tag ID has not been found')

    def test_api_infos_cid_bad(self):
        headers = {'Accept': 'application/json'}
        response = self.app.get(
            '/api/v1/infos/infos?cid=XYZ',
            headers=headers, status='*')
        self.assertEqual(response.status_int, 404)
        self.assertEqual(
            response.json['description'],
            'The cid is incorrectly formated')

    def test_api_infos_exclusive_parameters(self):
        headers = {'Accept': 'application/json'}
        response = self.app.get(
            '/api/v1/infos/infos?cid=XYZ&gid=ABC',
            headers=headers, status='*')
        self.assertEqual(response.status_int, 400)
        self.assertEqual(
            response.json['description'], 'cid and gid are exclusive')
        response = self.app.get(
            '/api/v1/infos/infos?pid=XYZ&tid=ABC',
            headers=headers, status='*')
        self.assertEqual(response.status_int, 400)
        self.assertEqual(
            response.json['description'], 'pid and tid are exclusive')


class TestGroupsController(FunctionalTest):

    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None
        cls.gi_by_emails_data = {
            "ampanman@baikinman.io":
                {"0000-0000": {
                    "name": "Ampanman",
                    "default-email": "ampanman@baikinman.io",
                    "emails": {
                        "ampanman@baikinman.io": {
                            "groups": {
                                "grp2": {}
                            }
                        }
                    }
                }}
        }

        def fake_get_idents_by_emails(cls, emails):
            ret = {}
            for email in emails:
                if email in cls.gi_by_emails_data.keys():
                    ret.update(copy.deepcopy(cls.gi_by_emails_data[email]))
                else:
                    ret.update({
                        email: {'name': None,
                                'default-email': email,
                                'emails': {}}})
            return ret

        cls.gi_by_emails = fake_get_idents_by_emails
        cls.groups = {
            "grp1": {
                "description": "The group 1",
                "emails": {
                    "john.doe@server.com": {},
                    "jane.doe@server.com": {
                        'end-date': '2016-01-01'}}},
            "grp2": {
                "description": "The group 2",
                "emails": {
                    "john.doe@server.com": {},
                    "ampanman@baikinman.io": {}}}}
        cls.gca = {"john.doe@server.com": "John Doe",
                   "jane.doe@server.com": "Jane Doe"}

    def test_get_groups(self):
        with patch.object(root.groups.Contributors, 'get_groups') as gg:
            with patch.object(
                    root.groups.Contributors,
                    'get_idents_by_emails') as gi_by_emails:
                with patch.object(
                        root.groups.Commits,
                        'get_commits_author_name_by_emails') as gca:
                    with patch.object(root.groups.Commits, 'get_repos') as gr:
                        gg.return_value = self.groups
                        gi_by_emails.side_effect = self.gi_by_emails
                        gca.return_value = self.gca
                        gr.return_value = (None, [])
                        response = self.app.get(
                            '/api/v1/groups/?withstats=true')
        assert response.status_int == 200
        expected_ret = {
            'grp2': {
                'description': 'The group 2',
                'domains': [],
                'members': {
                    'DgoOD1sIGwElFQQHGhEWSwUOGA--': {
                        'name': 'John Doe',
                        'gravatar': '46d19d53d565a1c3dd2f322f7b76c449',
                        # u'bounces': {}},
                        },
                    'VFVWUVhcRFRV': {
                        'name': 'Ampanman',
                        'gravatar': 'ad81b86bba0b59cc9e3d4d2896d67ca1',
                        # u'bounces': {}}
                        }
                },
                'projects_amount': 0,
                'repos_amount': 0,
            },
            'grp1': {
                'description': 'The group 1',
                'domains': [],
                'members': {
                    'DgQIBFsIGwElFQQHGhEWSwUOGA--': {
                        'name': 'Jane Doe',
                        'gravatar': '98685715b08980dac8b2379097c332f4',
                        # u'bounces': {
                        #    'end-date': '2016-01-01'}},
                        },
                    'DgoOD1sIGwElFQQHGhEWSwUOGA--': {
                        'name': 'John Doe',
                        'gravatar': '46d19d53d565a1c3dd2f322f7b76c449',
                        # u'bounces': {}}
                        }
                },
                'projects_amount': 0,
                'repos_amount': 0,
            }
        }
        self.assertDictEqual(response.json, expected_ret)

        with patch.object(root.groups.Contributors, 'get_groups') as gg:
            with patch.object(
                    root.groups.Contributors,
                    'get_idents_by_emails') as gi_by_emails:
                with patch.object(
                        root.groups.Commits,
                        'get_commits_author_name_by_emails') as gca:
                    with patch.object(root.groups.Commits, 'get_repos') as gr:
                        gg.return_value = self.groups
                        gi_by_emails.side_effect = self.gi_by_emails
                        gca.return_value = self.gca
                        gr.return_value = (None, [])
                        response = self.app.get(
                            '/api/v1/groups/?nameonly=true')
        assert response.status_int == 200
        expected_ret = {
            'grp2': None,
            'grp1': None,
        }
        self.assertDictEqual(response.json, expected_ret)

        with patch.object(root.groups.Contributors, 'get_groups') as gg:
            with patch.object(
                    root.groups.Contributors,
                    'get_idents_by_emails') as gi_by_emails:
                with patch.object(
                        root.groups.Commits,
                        'get_commits_author_name_by_emails') as gca:
                    with patch.object(root.groups.Commits, 'get_repos') as gr:
                        gg.return_value = self.groups
                        gi_by_emails.side_effect = self.gi_by_emails
                        gca.return_value = self.gca
                        gr.return_value = (None, [])
                        response = self.app.get('/api/v1/groups/?prefix=grp2')
        assert response.status_int == 200
        expected_ret = {
            'grp2': {
                'description': 'The group 2',
                'domains': [],
                'members': {
                    'DgoOD1sIGwElFQQHGhEWSwUOGA--': {
                        'name': 'John Doe',
                        'gravatar': '46d19d53d565a1c3dd2f322f7b76c449',
                        # u'bounces': {}},
                        },
                    'VFVWUVhcRFRV': {
                        'name': 'Ampanman',
                        'gravatar': 'ad81b86bba0b59cc9e3d4d2896d67ca1',
                        # u'bounces': {}}
                        }
                },
            }
        }
        self.assertDictEqual(response.json, expected_ret)


class TestUsersController(FunctionalTest):

    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None

        is_configured = MagicMock()
        is_configured.return_value = True
        root.users.AUTH_ENGINE.is_configured = is_configured

    def tearDown(self):
        self.con = index.Connector(index_suffix='users')
        self.con.ic.delete(index=self.con.index)
        FunctionalTest.tearDown(self)

    def test_users_crud_admin(self):
        headers = {
            'REMOTE_USER': 'admin',
            'ADMIN_TOKEN': '12345'}
        # User should not exist
        response = self.app.get(
            '/api/v1/users/admin', headers=headers, status="*")
        self.assertEqual(response.status_int, 404)

        # Push user details
        data = {
            'uid': 'admin',
            'name': 'saboten',
            'default-email': 'saboten@domain1',
            'emails': [
                {'email': 'saboten@domain1',
                 'groups': [
                     {'group': 'ugroup2',
                      'begin-date': '1410456005',
                      'end-date': '1410476005'}
                 ]}
            ]}
        response = self.app.put_json(
            '/api/v1/users/admin', data, headers=headers, status="*")
        self.assertEqual(response.status_int, 201)

        # Get admin user details
        response = self.app.get(
            '/api/v1/users/admin', headers=headers, status="*")
        self.assertEqual(response.status_int, 200)
        rdata = copy.deepcopy(data)
        rdata['cid'] = utils.encrypt(xorkey, 'saboten@domain1')
        self.assertDictEqual(response.json, rdata)

        # Update admin user details
        data['name'] = 'sabosan'
        response = self.app.post_json(
            '/api/v1/users/admin', data, headers=headers, status="*")
        self.assertEqual(response.status_int, 200)

        # Get admin user details
        response = self.app.get(
            '/api/v1/users/admin', headers=headers, status="*")
        self.assertEqual(response.status_int, 200)
        rdata = copy.deepcopy(data)
        rdata['cid'] = utils.encrypt(xorkey, 'saboten@domain1')
        self.assertDictEqual(response.json, rdata)

        # Get admin user details w/o admin_token
        headers = {'REMOTE_USER': 'admin'}
        response = self.app.get(
            '/api/v1/users/admin', headers=headers, status="*")
        self.assertEqual(response.status_int, 200)
        rdata = copy.deepcopy(data)
        rdata['cid'] = utils.encrypt(xorkey, 'saboten@domain1')
        self.assertDictEqual(response.json, rdata)

    def test_users_c_admin_wrong_token(self):
        data = {
            'uid': '1',
            'name': 'saboten',
            'default-email': 'saboten@domain1',
            'emails': []}
        headers = {
            'REMOTE_USER': 'admin',
            'ADMIN_TOKEN': 'WRONG'}
        response = self.app.put_json(
            '/api/v1/users/1', data, headers=headers, status="*")
        self.assertEqual(response.status_int, 401)

    def test_users_crud_user(self):
        # First set a user as admin
        data = {
            'uid': 'saboten',
            'name': 'Cactus Saboten',
            'default-email': 'saboten@domain1',
            'emails': [
                {'email': 'saboten@domain1',
                 'groups': [
                    {'group': 'ugroup2',
                     'begin-date': '1410456005',
                     'end-date': '1410476005'}
                     ]
                 }
            ]
        }

        headers = {
            'REMOTE_USER': 'admin',
            'ADMIN_TOKEN': '12345'}
        self.app.put_json(
            '/api/v1/users/saboten', data, headers=headers, status="*")

        # Change user
        headers = {'REMOTE_USER': 'saboten'}

        response = self.app.get(
            '/api/v1/users/saboten', headers=headers, status="*")
        self.assertEqual(response.status_int, 200)
        rdata = copy.deepcopy(data)
        rdata['cid'] = utils.encrypt(xorkey, 'saboten@domain1')
        self.assertDictEqual(response.json, rdata)

        # User is not authorized to change protected fields
        ndata = copy.deepcopy(data)
        ndata['default-email'] = 'saboten@domain2'
        response = self.app.post_json(
            '/api/v1/users/saboten', ndata, headers=headers, status="*")
        self.assertEqual(response.status_int, 403)

        # User is not authorized to change protected fields
        ndata = copy.deepcopy(data)
        ndata['emails'].append({'emails': 'new@email.com'})
        response = self.app.post_json(
            '/api/v1/users/saboten', ndata, headers=headers, status="*")
        self.assertEqual(response.status_int, 400)

        # Authorized to change its full name
        data['name'] = 'John Doe'
        response = self.app.post_json(
            '/api/v1/users/saboten', data, headers=headers, status="*")
        self.assertEqual(response.status_int, 200)

        # Not authorized to change its full name if > 100 chars
        ndata = copy.deepcopy(data)
        ndata['name'] = 'a'*101
        response = self.app.post_json(
            '/api/v1/users/saboten', ndata, headers=headers, status="*")
        self.assertEqual(response.status_int, 400)

        # Authorized to change its emails memberships
        email = [e for e in data['emails'] if
                 e['email'] == 'saboten@domain1'][0]
        email['groups'][0]['group'] = 'ugroup3'
        response = self.app.post_json(
            '/api/v1/users/saboten', data, headers=headers, status="*")
        self.assertEqual(response.status_int, 200)

        # Change user
        headers = {'REMOTE_USER': 'tokin'}

        # Another user not authorized to get
        response = self.app.get(
            '/api/v1/users/saboten', headers=headers, status="*")
        self.assertEqual(response.status_int, 401)

        # Another user not authorized to change
        data['name'] = 'John Doe'
        response = self.app.post_json(
            '/api/v1/users/saboten', data, headers=headers, status="*")
        self.assertEqual(response.status_int, 401)

        # Another user not authorized to delete
        response = self.app.delete(
            '/api/v1/users/saboten', headers=headers, status="*")
        self.assertEqual(response.status_int, 401)

        # Change user
        headers = {'REMOTE_USER': 'saboten'}

        # User authorized to delete itself
        response = self.app.delete(
            '/api/v1/users/saboten', headers=headers, status="*")
        self.assertEqual(response.status_int, 200)


class TestUsersControllerOpenIDConnect(FunctionalTest):

    def setUp(self):
        self.app = load_test_app(os.path.join(
            os.path.dirname(__file__),
            'fixtures/oidc_config.py'
        ))

    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None

        get_issuer_info = MagicMock()
        with open(os.path.join(os.path.dirname(__file__),
                               'fixtures/openid-configuration.json'),
                  'r') as oc:
            cls.issuer_info = json.load(oc)
            get_issuer_info.return_value = cls.issuer_info
        root.users.AUTH_ENGINE._get_issuer_info = get_issuer_info
        with open(os.path.join(os.path.dirname(__file__),
                               'fixtures/jwtRS256.key.pub'),
                  'r') as pubkey:
            cls.pubkey = pubkey.read()
        with open(os.path.join(os.path.dirname(__file__),
                               'fixtures/jwtRS256.key'),
                  'r') as privkey:
            cls.privkey = privkey.read()

        get_signing_key = MagicMock()
        get_signing_key.return_value = cls.pubkey
        root.users.AUTH_ENGINE._get_signing_key = get_signing_key

    def tearDown(self):
        self.con = index.Connector(index_suffix='users')
        self.con.ic.delete(index=self.con.index)
        FunctionalTest.tearDown(self)

    def create_token(self, claims):
        if 'iss' not in claims:
            claims['iss'] = self.issuer_info['issuer']
        if 'exp' not in claims:
            claims['exp'] = datetime.utcnow() + timedelta(seconds=3600)
        if 'aud' not in claims:
            claims['aud'] = 'repoxplorer'
        claims['iat'] = datetime.utcnow()
        token = jwt.encode(claims, self.privkey, algorithms='RS256',
                           headers={'kid': 'bababababa'})
        return token

    def test_users_crud_mapped_admin(self):
        token = self.create_token({'preferred_username': 'ampanman',
                                   'name': 'hero of justice',
                                   'sub': '123459876',
                                   'email': 'am@pan.man'})
        headers = {'Authorization': 'bearer %s' % token}
        # User should be created on the fly
        response = self.app.get(
            '/api/v1/users/ampanman', headers=headers, status="*")
        self.assertEqual(response.status_int, 200)
        root.users.AUTH_ENGINE._get_signing_key.assert_called_with(
            self.issuer_info['jwks_uri'],
            'bababababa')
        rdata = {'uid': 'ampanman',
                 'name': 'hero of justice',
                 'default-email': 'am@pan.man',
                 'emails': [{'email': 'am@pan.man'}]}
        rdata['cid'] = utils.encrypt(xorkey, 'am@pan.man')
        self.assertDictEqual(response.json, rdata, response.json)


class TestHistoController(FunctionalTest):

    @classmethod
    def setUpClass(cls):
        cls.con = index.Connector(index='repoxplorertest')
        cls.conp = index.Connector(
            index='repoxplorertest', index_suffix='projects')
        c = Commits(cls.con)
        c.add_commits(COMMITS)
        cls.db = set_projects_definition(cls.conp)

    @classmethod
    def tearDownClass(cls):
        cls.con.ic.delete(index=cls.con.index)
        cls.conp.ic.delete(index=cls.conp.index)
        if os.path.isdir(cls.db):
            shutil.rmtree(cls.db)

    def test_get_authors_histo(self):
        response = self.app.get('/api/v1/histo/authors?pid=test')
        assert response.status_int == 200
        self.assertEqual(response.json[0]['value'], 1)
        self.assertEqual(response.json[0]['date'], '2014-03-01')
        response = self.app.get(
            '/api/v1/histo/authors?pid=unknown', status="*")
        assert response.status_int == 404

    def test_get_commits_histo(self):
        response = self.app.get('/api/v1/histo/commits?pid=test')
        assert response.status_int == 200
        self.assertListEqual(
            response.json,
            [{'date': '2014-03-01', 'value': 1},
             {'date': '2014-04-01', 'value': 0},
             {'date': '2014-05-01', 'value': 0},
             {'date': '2014-06-01', 'value': 0},
             {'date': '2014-07-01', 'value': 0},
             {'date': '2014-08-01', 'value': 0},
             {'date': '2014-09-01', 'value': 2}]
        )


class TestInfosController(FunctionalTest):

    @classmethod
    def setUpClass(cls):
        cls.con = index.Connector(index='repoxplorertest')
        cls.conp = index.Connector(
            index='repoxplorertest', index_suffix='projects')
        c = Commits(cls.con)
        c.add_commits(COMMITS)
        cls.db = set_projects_definition(cls.conp)

    @classmethod
    def tearDownClass(cls):
        cls.con.ic.delete(index=cls.con.index)
        cls.conp.ic.delete(index=cls.conp.index)
        if os.path.isdir(cls.db):
            shutil.rmtree(cls.db)

    def test_get_infos(self):
        expected = {
            'first': 1393860653,
            'last': 1410456005,
            'commits_amount': 3,
            'authors_amount': 2,
            'line_modifieds_amount': 29,
            'duration': 16595352,
            'ttl_average': 0,
            'projects_amount': 1,
            'repos_amount': 1,
        }
        response = self.app.get('/api/v1/infos/infos?pid=test')
        self.assertEqual(response.status_int, 200)
        self.assertDictEqual(response.json, expected)

        # Check endpoint CSV mode
        response = self.app.get(
            '/api/v1/infos/infos?pid=test',
            headers={'Accept': 'text/csv'})
        self.assertEqual(response.status_int, 200)
        csvret = build_dict_from_csv(response.body)
        # Convert all dict values to str
        expected = dict((k, str(v)) for k, v in expected.items())
        self.assertDictEqual(csvret[0], expected)
        self.assertEqual(len(csvret), 1)

        # Make an attempt by setting meta ref to True
        new_projects_file = """
        project-templates:
          default:
            uri: https://github.com/nakata/%(name)s.git
            branches:
            - master

        projects:
          test:
            meta-ref: true
            repos:
              monkey:
                template: default
        """
        self.db = set_projects_definition(self.conp, new_projects_file)

        expected = {
            'first': 1393860653,
            'last': 1410456005,
            'commits_amount': 2,
            'authors_amount': 2,
            'line_modifieds_amount': 18,
            'duration': 16595352,
            'ttl_average': 0,
            'projects_amount': 1,
            'repos_amount': 1,
        }
        response = self.app.get('/api/v1/infos/infos?pid=test')
        self.assertEqual(response.status_int, 200)
        self.assertDictEqual(response.json, expected)

        # Test with a cid
        expected = {
            'projects_amount': 1,
            'first': 1410456005,
            'line_modifieds_amount': 10,
            'duration': 0,
            'commits_amount': 1,
            'ttl_average': 0,
            'last': 1410456005,
            'authors_amount': 1,
            'repos_amount': 1
        }
        cid = utils.encrypt(xorkey, 'n.suke@joker.org')
        response = self.app.get('/api/v1/infos/infos', {'cid': cid})
        self.assertEqual(response.status_int, 200)
        self.assertDictEqual(response.json, expected)

        # Validate we can request with a cid being a comma separated list
        # of emails
        cid = 'n.suke@joker.org,'
        response = self.app.get('/api/v1/infos/infos', {'cid': cid})
        self.assertEqual(response.status_int, 200)
        self.assertDictEqual(response.json, expected)

    def test_get_infos_contributor(self):
        expected = {
            'name': 'Nakata Daisuke',
            'mails_amount': 1,
            'gravatar': '505dcbea438008f24001e2928cdc0678',
        }
        cid = utils.encrypt(xorkey, 'n.suke@joker.org')
        response = self.app.get(
            '/api/v1/infos/contributor', {'cid': cid})
        self.assertEqual(response.status_int, 200)
        self.assertDictEqual(response.json, expected)


class TestStatusController(FunctionalTest):

    @classmethod
    def setUpClass(cls):
        cls.con = index.Connector(index='repoxplorertest')
        cls.conp = index.Connector(
            index='repoxplorertest', index_suffix='projects')
        c = Commits(cls.con)
        c.add_commits(COMMITS)
        cls.db = set_projects_definition(cls.conp)

    @classmethod
    def tearDownClass(cls):
        cls.con.ic.delete(index=cls.con.index)
        cls.conp.ic.delete(index=cls.conp.index)
        if os.path.isdir(cls.db):
            shutil.rmtree(cls.db)

    def test_get_version(self):
        expected = version.get_version()
        response = self.app.get('/api/v1/status/version')
        self.assertEqual(expected, response.json['version'])

    def test_get_status(self):
        expected = {
            'version': version.get_version(),
            'projects': 1,
            'repos': 1,
            'users_endpoint': False,
            'customtext': ''
        }
        response = self.app.get('/api/v1/status/status')
        self.assertEqual(expected, response.json)


class TestProjectsController(FunctionalTest):

    @classmethod
    def setUpClass(cls):
        cls.con = index.Connector(index='repoxplorertest')
        cls.conp = index.Connector(
            index='repoxplorertest', index_suffix='projects')
        c = Commits(cls.con)
        c.add_commits(COMMITS)
        projects_file = """
        project-templates:
          default:
            uri: https://github.com/nakata/%(name)s.git
            branches:
            - master

        projects:
          test:
            repos:
              monkey:
                template: default
          test2:
            repos:
              monkey:
                template: default
                tags:
                  - python
        """
        cls.db = set_projects_definition(cls.conp, projects_file)

    @classmethod
    def tearDownClass(cls):
        cls.con.ic.delete(index=cls.con.index)
        cls.conp.ic.delete(index=cls.conp.index)
        if os.path.isdir(cls.db):
            shutil.rmtree(cls.db)

    def test_get_projects(self):
        response = self.app.get('/api/v1/projects/projects')
        assert response.status_int == 200
        self.assertIn('test', response.json['projects'])
        self.assertIn('test2', response.json['projects'])

        response = self.app.get('/api/v1/projects/projects?pid=test')
        assert response.status_int == 200
        self.assertIn('test', response.json)
        self.assertNotIn('test2', response.json)

    def test_get_repos(self):
        response = self.app.get('/api/v1/projects/repos?pid=test')
        assert response.status_int == 200
        self.assertEqual(len(response.json), 1)
        self.assertEqual(response.json[0]['name'], 'monkey')
        response = self.app.get('/api/v1/projects/repos?tid=python')
        assert response.status_int == 200
        self.assertEqual(len(response.json), 1)
        self.assertEqual(response.json[0]['name'], 'monkey')


class TestTopsController(FunctionalTest):

    @classmethod
    def setUpClass(cls):
        cls.con = index.Connector(index='repoxplorertest')
        cls.conp = index.Connector(
            index='repoxplorertest', index_suffix='projects')
        c = Commits(cls.con)
        c.add_commits(COMMITS)
        cls.db = set_projects_definition(cls.conp)

    @classmethod
    def tearDownClass(cls):
        cls.con.ic.delete(index=cls.con.index)
        cls.conp.ic.delete(index=cls.conp.index)
        if os.path.isdir(cls.db):
            shutil.rmtree(cls.db)

    def test_get_tops_authors_bylchanged(self):
        expected_top1 = {
            'amount': 19,
            'gravatar': 'c184ebe163aa66b25668757000116849',
            'cid': utils.encrypt(xorkey, 'j.paul@joker.org'),
            'name': 'Jean Paul'
        }
        expected_top2 = {
            'amount': 10,
            'gravatar': '505dcbea438008f24001e2928cdc0678',
            'cid': utils.encrypt(xorkey, 'n.suke@joker.org'),
            'name': 'Nakata Daisuke'
        }
        response = self.app.get('/api/v1/tops/authors/bylchanged?pid=test')
        assert response.status_int == 200
        self.assertDictEqual(response.json[0], expected_top1)
        self.assertDictEqual(response.json[1], expected_top2)
        self.assertEqual(len(response.json), 2)
        # Same request but with a limit set to 1
        response = self.app.get(
            '/api/v1/tops/authors/bylchanged?pid=test&limit=1')
        assert response.status_int == 200
        self.assertDictEqual(response.json[0], expected_top1)
        self.assertEqual(len(response.json), 1)

        # Validate the CSV endpoint mode
        # First convert all expected dict values to str
        expected_top1 = dict((k, str(v)) for k, v in expected_top1.items())
        expected_top2 = dict((k, str(v)) for k, v in expected_top2.items())
        response = self.app.get(
            '/api/v1/tops/authors/bylchanged?pid=test',
            headers={'Accept': 'text/csv'})
        assert response.status_int == 200
        csvret = build_dict_from_csv(response.body)
        self.assertDictEqual(csvret[0], expected_top1)
        self.assertDictEqual(csvret[1], expected_top2)
        self.assertEqual(len(csvret), 2)

    def test_get_tops_authors_bycommits(self):
        expected_top1 = {
            'gravatar': 'c184ebe163aa66b25668757000116849',
            'amount': 3,
            'name': 'Jean Paul',
            'cid': utils.encrypt(xorkey, 'j.paul@joker.org'),
        }
        expected_top2 = {
            'gravatar': '505dcbea438008f24001e2928cdc0678',
            'amount': 1,
            'name': 'Nakata Daisuke',
            'cid': utils.encrypt(xorkey, 'n.suke@joker.org'),
        }
        response = self.app.get(
            '/api/v1/tops/authors/bycommits?pid=test&inc_merge_commit=on')
        assert response.status_int == 200
        self.assertDictEqual(response.json[0], expected_top1)
        self.assertDictEqual(response.json[1], expected_top2)
        self.assertEqual(len(response.json), 2)
        # Same request but with a limit set to 1
        response = self.app.get(
            '/api/v1/tops/authors/bycommits?pid=test'
            '&inc_merge_commit=on&limit=1')
        assert response.status_int == 200
        self.assertDictEqual(response.json[0], expected_top1)
        self.assertEqual(len(response.json), 1)

        # Validate the CSV endpoint mode
        # First convert all expected dict values to str
        expected_top1 = dict((k, str(v)) for k, v in expected_top1.items())
        expected_top2 = dict((k, str(v)) for k, v in expected_top2.items())
        response = self.app.get(
            '/api/v1/tops/authors/bycommits?'
            'pid=test&inc_merge_commit=on',
            headers={'Accept': 'text/csv'})
        assert response.status_int == 200
        csvret = build_dict_from_csv(response.body)
        self.assertDictEqual(csvret[0], expected_top1)
        self.assertDictEqual(csvret[1], expected_top2)
        self.assertEqual(len(csvret), 2)

    def test_get_tops_authors_diff(self):
        # with patch.object(root.projects.Projects, 'get_projects') as m:
        expected_diff = {
            'gravatar': '505dcbea438008f24001e2928cdc0678',
            'amount': 1,
            'name': 'Nakata Daisuke',
            'cid': utils.encrypt(xorkey, 'n.suke@joker.org'),
        }
        response = self.app.get(
            '/api/v1/tops/authors/diff?pid=test&dfromref=2014-01-01'
            '&dtoref=2014-09-03&dfrom=2014-09-04&dto=2017-01-01'
            '&inc_merge_commit=on&limit=1')
        assert response.status_int == 200
        self.assertDictEqual(response.json[0], expected_diff)
        self.assertEqual(len(response.json), 1)

    def test_get_tops_projects_bycommits(self):
        cid = utils.encrypt(xorkey, 'j.paul@joker.org')
        response = self.app.get(
            '/api/v1/tops/projects/bycommits?cid=%s' % cid)
        expected_top1 = {
            'amount': 2,
            'name': 'test'
        }
        assert response.status_int == 200
        self.assertDictEqual(response.json[0], expected_top1)
        self.assertEqual(len(response.json), 1)
        # Ask repo details
        response = self.app.get(
            '/api/v1/tops/projects/bycommits?cid='
            '%s&inc_repos_detail=true' % cid)
        expected_top1_d = {
            'amount': 2,
            'name': 'monkey:master',
            'projects': ['test']
        }
        assert response.status_int == 200
        self.assertDictEqual(response.json[0], expected_top1_d)
        self.assertEqual(len(response.json), 1)
        # Check the limit attribute
        response = self.app.get(
            '/api/v1/tops/projects/bycommits?cid=%s&limit=0' % cid)
        assert response.status_int == 200
        self.assertEqual(len(response.json), 0)

        # Validate the CSV endpoint mode
        # First convert all expected dict values to str
        expected_top1 = dict((k, str(v)) for k, v in expected_top1.items())
        for k, v in expected_top1_d.items():
            if isinstance(v, list):
                # A list, that will be semi column separated, can be return
                # when inc_repos_detail is passed to this endpoint
                expected_top1_d[k] = ";".join(v)
            else:
                expected_top1_d[k] = str(v)
        response = self.app.get(
            '/api/v1/tops/projects/bycommits?'
            'cid=%s' % cid,
            headers={'Accept': 'text/csv'})
        assert response.status_int == 200
        csvret = build_dict_from_csv(response.body)
        self.assertDictEqual(csvret[0], expected_top1)
        response = self.app.get(
            '/api/v1/tops/projects/bycommits?'
            'cid=%s&inc_repos_detail=true' % cid,
            headers={'Accept': 'text/csv'})
        assert response.status_int == 200
        csvret = build_dict_from_csv(response.body)
        self.assertDictEqual(csvret[0], expected_top1_d)

    def test_get_tops_projects_bylchanged(self):
        cid = utils.encrypt(xorkey, 'j.paul@joker.org')
        response = self.app.get(
            '/api/v1/tops/projects/bylchanged?cid=%s' % cid)
        expected_top1 = {
            'amount': 19,
            'name': 'test'
        }
        assert response.status_int == 200
        self.assertDictEqual(response.json[0], expected_top1)
        self.assertEqual(len(response.json), 1)
        # Ask repo details
        response = self.app.get(
            '/api/v1/tops/projects/bylchanged?cid='
            '%s&inc_repos_detail=true' % cid)
        expected_top1_d = {
            'amount': 19,
            'name': 'monkey:master',
            'projects': ['test']
        }
        assert response.status_int == 200
        self.assertDictEqual(response.json[0], expected_top1_d)
        self.assertEqual(len(response.json), 1)
        # Check the limit attribute
        response = self.app.get(
            '/api/v1/tops/projects/bylchanged?cid=%s&limit=0' % cid)
        assert response.status_int == 200
        self.assertEqual(len(response.json), 0)

        # Validate the CSV endpoint mode
        # First convert all expected dict values to str
        expected_top1 = dict((k, str(v)) for k, v in expected_top1.items())
        for k, v in expected_top1_d.items():
            if isinstance(v, list):
                # A list, that will be semi column separated, can be return
                # when inc_repos_detail is passed to this endpoint
                expected_top1_d[k] = ";".join(v)
            else:
                expected_top1_d[k] = str(v)
        response = self.app.get(
            '/api/v1/tops/projects/bylchanged?'
            'cid=%s' % cid,
            headers={'Accept': 'text/csv'})
        assert response.status_int == 200
        csvret = build_dict_from_csv(response.body)
        self.assertDictEqual(csvret[0], expected_top1)
        response = self.app.get(
            '/api/v1/tops/projects/bylchanged?'
            'cid=%s&inc_repos_detail=true' % cid,
            headers={'Accept': 'text/csv'})
        assert response.status_int == 200
        csvret = build_dict_from_csv(response.body)
        self.assertDictEqual(csvret[0], expected_top1_d)


class TestSearchController(FunctionalTest):

    @classmethod
    def setUpClass(cls):
        cls.con = index.Connector(index='repoxplorertest')
        cls.c = Commits(cls.con)
        cls.c.add_commits(COMMITS)

    @classmethod
    def tearDownClass(cls):
        cls.con.ic.delete(index=cls.con.index)

    def test_search_authors(self):
        root.search.indexname = 'repoxplorertest'
        response = self.app.get('/api/v1/search/search_authors?query=jean')
        cid = utils.encrypt(xorkey, 'j.paul@joker.org')
        expected = {
            cid: {'name': 'Jean Paul',
                  'gravatar': 'c184ebe163aa66b25668757000116849'}}
        self.assertDictEqual(response.json, expected)


class TestMetadataController(FunctionalTest):

    def setUp(self):
        FunctionalTest.setUp(self)
        self.con = index.Connector(index='repoxplorertest')
        self.conp = index.Connector(
            index='repoxplorertest', index_suffix='projects')
        c = Commits(self.con)
        c.add_commits(COMMITS)
        self.db = set_projects_definition(self.conp)

    def tearDown(self):
        FunctionalTest.tearDown(self)
        self.con.ic.delete(index=self.con.index)
        self.conp.ic.delete(index=self.conp.index)
        if os.path.isdir(self.db):
            shutil.rmtree(self.db)

    def test_get_metadata(self):
        response = self.app.get('/api/v1/metadata/metadata?pid=test')
        assert response.status_int == 200
        self.assertDictEqual(
            response.json,
            {'implement': 3, 'close-bug': 1})
        response = self.app.get(
            '/api/v1/metadata/metadata?key=implement&pid=test')
        assert response.status_int == 200
        self.assertIn('feature 1', response.json)
        self.assertIn('feature 35', response.json)
        self.assertIn('feature 36', response.json)
        self.assertEqual(len(response.json), 3)


class TestTagsController(FunctionalTest):

    @classmethod
    def setUpClass(cls):
        cls.con = index.Connector(index='repoxplorertest')
        cls.conp = index.Connector(
            index='repoxplorertest', index_suffix='projects')
        c = Commits(cls.con)
        c.add_commits(COMMITS)
        cls.db = set_projects_definition(cls.conp)
        t = Tags(index.Connector(
            index='repoxplorertest', index_suffix='tags'))
        tags = [
            {
                'sha': '3597334f2cb10772950c97ddf2f6cc17b184',
                'date': 1410456005,
                'repo':
                    'https://github.com/nakata/monkey.git:monkey',
                'name': 'tag1',
            },
            {
                'sha': '3597334f2cb10772950c97ddf2f6cc17b1845',
                'date': 1410456005,
                'repo':
                    'https://github.com/nakata/monkey.git:monkey',
                'name': 'tag2',
            }]
        t.add_tags(tags)

    @classmethod
    def tearDownClass(cls):
        cls.con.ic.delete(index=cls.con.index)
        cls.conp.ic.delete(index=cls.conp.index)
        if os.path.isdir(cls.db):
            shutil.rmtree(cls.db)

    def test_get_tags(self):
        response = self.app.get('/api/v1/tags/tags?pid=test')
        assert response.status_int == 200
        tag1 = [t for t in response.json if t['name'] == 'tag1'][0]
        tag2 = [t for t in response.json if t['name'] == 'tag2'][0]
        self.assertDictEqual(tag2, {
            'name': 'tag2',
            'sha': '3597334f2cb10772950c97ddf2f6cc17b1845',
            'date': 1410456005,
            'repo':
                'https://github.com/nakata/monkey.git:monkey'})
        self.assertDictEqual(tag1, {
            'name': 'tag1',
            'sha': '3597334f2cb10772950c97ddf2f6cc17b184',
            'date': 1410456005,
            'repo':
                'https://github.com/nakata/monkey.git:monkey'})

    def test_get_tags_with_user_def_releases(self):
        new_projects_file = """
        project-templates:
          default:
            uri: https://github.com/nakata/%(name)s.git
            branches:
            - master
            releases:
            - name: '1.0'
              date: 2019-01-01

        projects:
          test:
            releases:
            - name: ocata
              date: 2017-02-22
            repos:
              monkey:
                template: default
        """
        self.db = set_projects_definition(self.conp, new_projects_file)
        response = self.app.get('/api/v1/tags/tags?pid=test')
        assert response.status_int == 200
        self.assertEqual(len(response.json), 4)
        udt = [t for t in response.json if t['name'] == '1.0'][0]
        udt2 = [t for t in response.json if t['name'] == 'ocata'][0]
        self.assertEqual('1.0', udt['name'])
        self.assertEqual('ocata', udt2['name'])


class TestCommitsController(FunctionalTest):

    @classmethod
    def setUpClass(cls):
        cls.con = index.Connector(index='repoxplorertest')
        cls.conp = index.Connector(
            index='repoxplorertest', index_suffix='projects')
        c = Commits(cls.con)
        c.add_commits(COMMITS)
        cls.db = set_projects_definition(cls.conp)

    @classmethod
    def tearDownClass(cls):
        cls.con.ic.delete(index=cls.con.index)
        cls.conp.ic.delete(index=cls.conp.index)
        if os.path.isdir(cls.db):
            shutil.rmtree(cls.db)

    def test_input_filter_validation(self):
        response = self.app.get(
            '/api/v1/commits/commits?pid=invalid', status="*")
        assert response.status_int == 404

        response = self.app.get(
            '/api/v1/commits/commits?pid=test&dfrom=invalid', status="*")
        assert response.status_int == 400

    def test_get_commits(self):
        response = self.app.get('/api/v1/commits/commits?pid=test')
        assert response.status_int == 200
        self.assertEqual(response.json[2][0]['author_name'],
                         'Nakata Daisuke')
        self.assertIn('test', response.json[2][0]['projects'])
        self.assertEqual(len(response.json[2][0]['projects']), 1)

        response = self.app.get(
            '/api/v1/commits/commits?pid=test&'
            'metadata=implement:feature 35')
        assert response.status_int == 200
        self.assertEqual(response.json[2][0]['author_name'],
                         'Nakata Daisuke')

        response = self.app.get(
            '/api/v1/commits/commits?pid=test&'
            'metadata=implement:feature 36')
        assert response.status_int == 200
        self.assertEqual(response.json[2][0]['author_name'],
                         'Jean Paul')

        response = self.app.get(
            '/api/v1/commits/commits?pid=test&metadata='
            'implement:feature 36,close-bug:18')
        assert response.status_int == 200
        self.assertEqual(response.json[2][0]['author_name'],
                         'Jean Paul')

        response = self.app.get(
            '/api/v1/commits/commits?pid=test&'
            'metadata=implement:*')
        assert response.status_int == 200
        self.assertEqual(response.json[1], 3)

        response = self.app.get(
            '/api/v1/commits/commits?pid=test&'
            'inc_merge_commit=on')
        assert response.status_int == 200
        self.assertEqual(response.json[1], 4)

    def test_get_commits_with_groups_filter(self):
        with patch.object(root.groups.Contributors, 'get_groups') as gg:
            gg.return_value = GROUPS
            response = self.app.get(
                '/api/v1/commits/commits?pid=test&exc_groups=grp1')
            assert response.status_int == 200
            self.assertEqual(response.json[1], 1)
            self.assertEqual(
                response.json[2][0]['author_name'],
                'Nakata Daisuke')
            response = self.app.get(
                '/api/v1/commits/commits?pid=test&inc_groups=grp2')
            assert response.status_int == 200
            self.assertEqual(response.json[1], 1)
            self.assertEqual(
                response.json[2][0]['author_name'],
                'Nakata Daisuke')

    def test_get_commits_with_bot_groups(self):
        new_projects_file = """
        project-templates:
          default:
            uri: https://github.com/nakata/%(name)s.git
            branches:
            - master

        projects:
          test:
            bots-group: grp1
            repos:
              monkey:
                template: default
        """
        self.db = set_projects_definition(self.conp, new_projects_file)
        with patch.object(root.groups.Contributors, 'get_groups') as gg:
            gg.return_value = GROUPS
            response = self.app.get(
                '/api/v1/commits/commits?pid=test')
            assert response.status_int == 200
            self.assertEqual(response.json[1], 1)
            self.assertEqual(
                response.json[2][0]['author_name'],
                'Nakata Daisuke')
