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

from repoxplorer import index
from repoxplorer.tests import FunctionalTest
from repoxplorer.index.commits import Commits
from repoxplorer.index.tags import Tags

from repoxplorer import version
from repoxplorer.controllers import root
from repoxplorer.controllers import utils

from mock import patch
from contextlib import nested

from StringIO import StringIO

from pecan import conf

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
            'meta-ref: test'],
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
    buf = StringIO(body)
    raw_fields = buf.readlines()[0]
    fields = raw_fields.strip().split(',')
    buf.seek(len(raw_fields))
    r = csv.DictReader(buf, fields)
    ret = []
    for row in r:
        ret.append(row)
    return ret


class TestErrorController(FunctionalTest):

    @classmethod
    def setUpClass(cls):
        cls.con = index.Connector(index='repoxplorertest')
        cls.c = Commits(cls.con)
        cls.c.add_commits(COMMITS)
        cls.projects = {
            'test': {
                'repos': [
                    {'uri': 'https://github.com/nakata/monkey.git',
                     'name': 'monkey',
                     'branch': 'master'}]
            }
        }

    @classmethod
    def tearDownClass(cls):
        cls.con.ic.delete(index=cls.con.index)

    def test_api_infos_pid_not_found(self):
        with patch.object(root.projects.Projects, 'get_projects') as m:
            root.indexname = 'repoxplorertest'
            m.return_value = self.projects
            headers = {'Accept': 'application/json'}
            response = self.app.get(
                '/api/v1/infos/infos?pid=notexists',
                headers=headers, status='*')
        self.assertEqual(response.status_int, 404)
        self.assertEqual(
            response.json['description'],
            'The project has not been found')

    def test_api_project_repos_pid_not_found(self):
        with patch.object(root.projects.Projects, 'get_projects') as m:
            root.indexname = 'repoxplorertest'
            m.return_value = self.projects
            headers = {'Accept': 'application/json'}
            response = self.app.get(
                '/api/v1/projects/repos?pid=notexists',
                headers=headers, status='*')
        self.assertEqual(response.status_int, 404)
        self.assertEqual(
            response.json['description'],
            'Project ID or Tag ID has not been found')

    def test_api_infos_cid_bad(self):
        with patch.object(root.projects.Projects, 'get_projects') as m:
            root.indexname = 'repoxplorertest'
            m.return_value = self.projects
            headers = {'Accept': 'application/json'}
            response = self.app.get(
                '/api/v1/infos/infos?cid=XYZ',
                headers=headers, status='*')
        self.assertEqual(response.status_int, 404)
        self.assertEqual(
            response.json['description'],
            'The cid is incorrectly formated')

    def test_api_infos_exclusive_parameters(self):
        with patch.object(root.projects.Projects, 'get_projects') as m:
            root.indexname = 'repoxplorertest'
            m.return_value = self.projects
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
        patches = [patch.object(root.groups.Contributors,
                                'get_groups'),
                   patch.object(root.groups.Contributors,
                                'get_idents_by_emails'),
                   patch.object(root.groups.Commits,
                                'get_commits_author_name_by_emails'),
                   patch.object(root.groups.tops.TopProjectsController,
                                'gbycommits')]
        with nested(*patches) as (gg, gi_by_emails, gca, gby_commits):
            gg.return_value = self.groups
            gi_by_emails.side_effect = self.gi_by_emails
            gca.return_value = self.gca
            response = self.app.get('/api/v1/groups/?withstats=true')
            assert response.status_int == 200
            expected_ret = {
                u'grp2': {
                    u'description': u'The group 2',
                    u'domains': [],
                    u'members': {
                        u'DgoOD1sIGwElFQQHGhEWSwUOGA--': {
                            u'name': u'John Doe',
                            u'gravatar': u'46d19d53d565a1c3dd2f322f7b76c449',
                            # u'bounces': {}},
                            },
                        u'VFVWUVhcRFRV': {
                            u'name': u'Ampanman',
                            u'gravatar': u'ad81b86bba0b59cc9e3d4d2896d67ca1',
                            # u'bounces': {}}
                            }
                    },
                    u'projects_amount': 0,
                    u'repos_amount': 0,
                },
                u'grp1': {
                    u'description': u'The group 1',
                    u'domains': [],
                    u'members': {
                        u'DgQIBFsIGwElFQQHGhEWSwUOGA--': {
                            u'name': u'Jane Doe',
                            u'gravatar': u'98685715b08980dac8b2379097c332f4',
                            # u'bounces': {
                            #    'end-date': '2016-01-01'}},
                            },
                        u'DgoOD1sIGwElFQQHGhEWSwUOGA--': {
                            u'name': u'John Doe',
                            u'gravatar': u'46d19d53d565a1c3dd2f322f7b76c449',
                            # u'bounces': {}}
                            }
                    },
                    u'projects_amount': 0,
                    u'repos_amount': 0,
                }
            }
            self.assertDictEqual(response.json, expected_ret)
            response = self.app.get('/api/v1/groups/?nameonly=true')
            assert response.status_int == 200
            expected_ret = {
                u'grp2': None,
                u'grp1': None,
            }
            self.assertDictEqual(response.json, expected_ret)
            response = self.app.get(
                '/api/v1/groups/?prefix=grp2')
            assert response.status_int == 200
            expected_ret = {
                u'grp2': {
                    u'description': u'The group 2',
                    u'domains': [],
                    u'members': {
                        u'DgoOD1sIGwElFQQHGhEWSwUOGA--': {
                            u'name': u'John Doe',
                            u'gravatar': u'46d19d53d565a1c3dd2f322f7b76c449',
                            # u'bounces': {}},
                            },
                        u'VFVWUVhcRFRV': {
                            u'name': u'Ampanman',
                            u'gravatar': u'ad81b86bba0b59cc9e3d4d2896d67ca1',
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
        root.users.indexname = 'repoxplorertest'
        root.users.endpoint_active = True
        root.users.admin_token = '12345'

    def tearDown(self):
        self.con = index.Connector(
            index=root.users.indexname, index_suffix='users')
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


class TestHistoController(FunctionalTest):

    @classmethod
    def setUpClass(cls):
        cls.con = index.Connector(index='repoxplorertest')
        cls.projects = {
            'test': {
                'repos': [
                    {'uri': 'https://github.com/nakata/monkey.git',
                     'name': 'monkey',
                     'branch': 'master'}]
            }
        }
        cls.c = Commits(cls.con)
        cls.c.add_commits(COMMITS)

    @classmethod
    def tearDownClass(cls):
        cls.con.ic.delete(index=cls.con.index)

    def test_get_authors_histo(self):
        with patch.object(root.projects.Projects, 'get_projects') as m:
            root.histo.indexname = 'repoxplorertest'
            m.return_value = self.projects
            response = self.app.get('/api/v1/histo/authors?pid=test')
        assert response.status_int == 200
        self.assertEqual(response.json[0]['value'], 1)
        self.assertEqual(response.json[0]['date'], '2014-03-01')

        with patch.object(root.projects.Projects, 'get_projects') as m:
            root.histo.indexname = 'repoxplorertest'
            m.return_value = self.projects
            response = self.app.get(
                '/api/v1/histo/authors?pid=unknown', status="*")
        assert response.status_int == 404

    def test_get_commits_histo(self):
        with patch.object(root.projects.Projects, 'get_projects') as m:
            root.histo.indexname = 'repoxplorertest'
            m.return_value = self.projects
            response = self.app.get('/api/v1/histo/commits?pid=test')
        assert response.status_int == 200
        self.assertListEqual(
            response.json,
            [{u'date': u'2014-03-01', u'value': 1},
             {u'date': u'2014-04-01', u'value': 0},
             {u'date': u'2014-05-01', u'value': 0},
             {u'date': u'2014-06-01', u'value': 0},
             {u'date': u'2014-07-01', u'value': 0},
             {u'date': u'2014-08-01', u'value': 0},
             {u'date': u'2014-09-01', u'value': 2}]
        )


class TestInfosController(FunctionalTest):

    @classmethod
    def setUpClass(cls):
        cls.con = index.Connector(index='repoxplorertest')
        cls.projects = {
            'test': {
                'repos': [
                    {'uri': 'https://github.com/nakata/monkey.git',
                     'name': 'monkey',
                     'branch': 'master'}]
            }
        }
        cls.c = Commits(cls.con)
        cls.c.add_commits(COMMITS)

    @classmethod
    def tearDownClass(cls):
        cls.con.ic.delete(index=cls.con.index)

    def test_get_infos(self):
        expected = {
            'first': 1393860653,
            'last': 1410456005,
            'commits_amount': 3,
            'authors_amount': 2,
            'line_modifieds_amount': 29,
            'duration': 16595352,
            'ttl_average': 0
        }
        with patch.object(root.projects.Projects, 'get_projects') as m:
            root.infos.indexname = 'repoxplorertest'
            m.return_value = self.projects
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
            expected = {
                'first': 1393860653,
                'last': 1410456005,
                'commits_amount': 2,
                'authors_amount': 2,
                'line_modifieds_amount': 18,
                'duration': 16595352,
                'ttl_average': 0
            }
            projects_with_meta_ref = copy.deepcopy(self.projects)
            projects_with_meta_ref['test']['meta_ref'] = True
            m.return_value = projects_with_meta_ref
            response = self.app.get('/api/v1/infos/infos?pid=test')
            self.assertEqual(response.status_int, 200)
            self.assertDictEqual(response.json, expected)

    def test_get_infos_contributor(self):
        expected = {
            'repos_amount': 1,
            'name': 'Nakata Daisuke',
            'mails_amount': 1,
            'gravatar': '505dcbea438008f24001e2928cdc0678',
            'projects_amount': 1
        }
        cid = utils.encrypt(xorkey, 'n.suke@joker.org')
        with patch.object(root.projects.Projects, 'get_projects') as m:
            root.infos.indexname = 'repoxplorertest'
            m.return_value = self.projects
            response = self.app.get(
                '/api/v1/infos/contributor?cid=%s' % cid)
            self.assertEqual(response.status_int, 200)
            self.assertDictEqual(response.json, expected)


class TestStatusController(FunctionalTest):
    @classmethod
    def setUpClass(cls):
        cls.projects = {
            'test': {
                'repos': [
                    {'uri': 'https://github.com/nakata/monkey.git',
                     'name': 'monkey',
                     'branch': 'master'}]
            }
        }

    def test_get_version(self):
        expected = version.get_version()
        response = self.app.get('/api/v1/status/version')
        self.assertEqual(expected, response.json['version'])

    def test_get_status(self):
        with patch.object(root.projects.Projects, 'get_projects') as m:
            m.return_value = self.projects
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
        cls.projects = {
            'test': {
                'repos': [
                    {'uri': 'https://github.com/nakata/monkey.git',
                     'name': 'monkey',
                     'branch': 'master',
                     'tags': ['python']}
                ]
            }
        }

    def test_get_projects(self):
        with patch.object(root.projects.Projects, 'get_projects') as m:
            m.return_value = self.projects
            response = self.app.get('/api/v1/projects/projects')
            assert response.status_int == 200
            self.assertIn('test', response.json['projects'])

    def test_get_repos(self):
        with patch.object(root.projects.Projects, 'get_projects') as m:
            m.return_value = self.projects
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
        cls.projects = {
            'test': {
                'repos': [
                    {'uri': 'https://github.com/nakata/monkey.git',
                     'name': 'monkey',
                     'branch': 'master'}]
            }
        }
        cls.c = Commits(cls.con)
        cls.c.add_commits(COMMITS)

    @classmethod
    def tearDownClass(cls):
        cls.con.ic.delete(index=cls.con.index)

    def test_get_tops_authors_bylchanged(self):
        with patch.object(root.projects.Projects, 'get_projects') as m:
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
            m.return_value = self.projects
            root.tops.indexname = 'repoxplorertest'
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
        with patch.object(root.projects.Projects, 'get_projects') as m:
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
            m.return_value = self.projects
            root.tops.indexname = 'repoxplorertest'
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
        with patch.object(root.projects.Projects, 'get_projects') as m:
            expected_diff = {
                'gravatar': '505dcbea438008f24001e2928cdc0678',
                'amount': 1,
                'name': 'Nakata Daisuke',
                'cid': utils.encrypt(xorkey, 'n.suke@joker.org'),
            }
            m.return_value = self.projects
            root.tops.indexname = 'repoxplorertest'
            response = self.app.get(
                '/api/v1/tops/authors/diff?pid=test&dfromref=2014-01-01'
                '&dtoref=2014-09-03&dfrom=2014-09-04&dto=2017-01-01'
                '&inc_merge_commit=on&limit=1')
            assert response.status_int == 200
            self.assertDictEqual(response.json[0], expected_diff)
            self.assertEqual(len(response.json), 1)

    def test_get_tops_projects_bycommits(self):
        cid = utils.encrypt(xorkey, 'j.paul@joker.org')
        with patch.object(root.projects.Projects, 'get_projects') as m:
            m.return_value = self.projects
            root.tops.indexname = 'repoxplorertest'
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
        with patch.object(root.projects.Projects, 'get_projects') as m:
            m.return_value = self.projects
            root.tops.indexname = 'repoxplorertest'
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
            cid: {u'name': 'Jean Paul',
                  u'gravatar': u'c184ebe163aa66b25668757000116849'}}
        self.assertDictEqual(response.json, expected)


class TestMetadataController(FunctionalTest):

    @classmethod
    def setUpClass(cls):
        cls.con = index.Connector(index='repoxplorertest')
        cls.projects = {
            'test': {
                'repos': [
                    {'uri': 'https://github.com/nakata/monkey.git',
                     'name': 'monkey',
                     'branch': 'master'}]
            }
        }
        cls.c = Commits(cls.con)
        cls.c.add_commits(COMMITS)

    @classmethod
    def tearDownClass(cls):
        cls.con.ic.delete(index=cls.con.index)

    def test_get_metadata(self):
        with patch.object(root.projects.Projects, 'get_projects') as m:
            m.return_value = self.projects
            root.metadata.indexname = 'repoxplorertest'
            response = self.app.get('/api/v1/metadata/metadata?pid=test')
            assert response.status_int == 200
            self.assertDictEqual(
                response.json,
                {u'implement': 3, u'close-bug': 1})
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
        cls.t = Tags(cls.con)
        cls.tags = [
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
        cls.t.add_tags(cls.tags)
        cls.projects = {
            'test': {
                'repos': [
                    {'uri': 'https://github.com/nakata/monkey.git',
                     'name': 'monkey',
                     'branch': 'master'}]
            }
        }

    @classmethod
    def tearDownClass(cls):
        cls.con.ic.delete(index=cls.con.index)

    def test_get_tags(self):
        with patch.object(root.projects.Projects, 'get_projects') as m:
            m.return_value = self.projects
            root.tags.indexname = 'repoxplorertest'
            response = self.app.get('/api/v1/tags/tags?pid=test')
            assert response.status_int == 200
            tag1 = [t for t in response.json if t['name'] == 'tag1'][0]
            tag2 = [t for t in response.json if t['name'] == 'tag2'][0]
            self.assertDictEqual(tag2, {
                u'name': u'tag2',
                u'sha': u'3597334f2cb10772950c97ddf2f6cc17b1845',
                u'date': 1410456005,
                u'repo':
                    u'https://github.com/nakata/monkey.git:monkey'})
            self.assertDictEqual(tag1, {
                u'name': u'tag1',
                u'sha': u'3597334f2cb10772950c97ddf2f6cc17b184',
                u'date': 1410456005,
                u'repo':
                    u'https://github.com/nakata/monkey.git:monkey'})


class TestCommitsController(FunctionalTest):

    @classmethod
    def setUpClass(cls):
        cls.con = index.Connector(index='repoxplorertest')
        cls.c = Commits(cls.con)
        cls.c.add_commits(COMMITS)
        cls.projects = {
            'test': {
                'repos': [
                    {'uri': 'https://github.com/nakata/monkey.git',
                     'name': 'monkey',
                     'branch': 'master'}]
            }
        }

    @classmethod
    def tearDownClass(cls):
        cls.con.ic.delete(index=cls.con.index)

    def test_input_filter_validation(self):
        with patch.object(root.projects.Projects, 'get_projects') as m:
            root.commits.indexname = 'repoxplorertest'
            m.return_value = self.projects

            response = self.app.get(
                '/api/v1/commits/commits?pid=invalid', status="*")
            assert response.status_int == 404

            response = self.app.get(
                '/api/v1/commits/commits?pid=test&dfrom=invalid', status="*")
            assert response.status_int == 400

    def test_get_commits(self):
        with patch.object(root.projects.Projects, 'get_projects') as m:
            root.commits.indexname = 'repoxplorertest'
            m.return_value = self.projects

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
        patches = [
            patch.object(root.projects.Projects, 'get_projects'),
            patch.object(root.groups.Contributors, 'get_groups')]
        with nested(*patches) as (gp, gg):
            root.commits.indexname = 'repoxplorertest'
            gp.return_value = self.projects
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
