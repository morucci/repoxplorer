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


from repoxplorer import index
from repoxplorer.tests import FunctionalTest
from repoxplorer.index.commits import Commits
from repoxplorer.index.tags import Tags

from repoxplorer import version
from repoxplorer.controllers import root
from repoxplorer.controllers import utils

from mock import patch
from contextlib import nested

from pecan import conf

xorkey = conf.get('xorkey') or 'default'

COMMITS = [
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
            'https://github.com/nakata/monkey.git:monkey:master', ],
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
        'line_modifieds': 10,
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
        'author_name': 'Jean Marc',
        'committer_name': 'Jean Marc',
        'author_email': 'j.marc@joker2.org',
        'committer_email': 'j.marc@joker2.org',
        'repos': [
            'https://github.com/nakata/monkey.git:monkey:master', ],
        'line_modifieds': 0,
        'merge_commit': True,
        'commit_msg': 'Merge: something',
    }]


class TestRootController(FunctionalTest):

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
        cls.groups = {
            "grp1": {
                "description": "The group 1",
                "emails": {
                    "j.paul@joker.org": {},
                    "j.marc@joker2.org": {}}}}

    @classmethod
    def tearDownClass(cls):
        cls.con.ic.delete(index=cls.con.index)

    def test_get_index(self):
        response = self.app.get('/')
        assert response.status_int == 200

    def test_get_projects_page(self):
        response = self.app.get('/projects.html')
        assert response.status_int == 200

    def test_get_project_page(self):
        with patch.object(root.Projects, 'get_projects') as m:
            root.indexname = 'repoxplorertest'
            m.return_value = self.projects
            response = self.app.get('/project.html?pid=test')
        assert response.status_int == 200

    def test_get_group_page(self):
        with patch.object(root.Projects, 'get_projects') as m:
            with patch.object(root.groups.Contributors, 'get_groups') as g:
                root.indexname = 'repoxplorertest'
                m.return_value = self.projects
                g.return_value = self.groups
                response = self.app.get('/group.html?gid=grp1')
        assert response.status_int == 200

    def test_get_contributor_page(self):
        cid = utils.encrypt(xorkey, 'n.suke@joker.org')
        with patch.object(root.Projects, 'get_projects') as m:
            root.indexname = 'repoxplorertest'
            m.return_value = self.projects
            response = self.app.get('/contributor.html?cid=%s' % cid)
        assert response.status_int == 200

    def test_get_contributors_page(self):
        root.indexname = 'repoxplorertest'
        response = self.app.get('/contributors.html')
        assert response.status_int == 200


class TestGroupsController(FunctionalTest):

    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None
        cls.gi_by_email_data = {
            "ampanman@baikinman.io":
                ("0000-0000", {
                    "name": "Ampanman",
                    "default-email": "ampanman@baikinman.io",
                    "emails": {
                        "ampanman@baikinman.io": {
                            "groups": {
                                "grp2": {}
                            }
                        }
                    }
                })
        }
        cls.gi_by_email = lambda _, email: cls.gi_by_email_data.get(email) or (
            email, {'name': None,
                    'default-email': email,
                    'emails': {}})
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
                                'get_ident_by_email'),
                   patch.object(root.groups.Commits,
                                'get_commits_author_name_by_emails')]
        with nested(*patches) as (gg, gi_by_email, gca):
            gg.return_value = self.groups
            gi_by_email.side_effect = self.gi_by_email
            gca.return_value = self.gca
            response = self.app.get('/api/v1/groups/')
            assert response.status_int == 200
            expected_ret = {
                u'grp2': {
                    u'description': u'The group 2',
                    u'domains': [],
                    u'members': {
                        u'DgoOD1sIGwElFQQHGhEWSwUOGA--': {
                            u'name': u'John Doe',
                            u'gravatar': u'46d19d53d565a1c3dd2f322f7b76c449',
                            u'bounces': {}},
                        u'VFVWUVhcRFRV': {
                            u'name': u'Ampanman',
                            u'gravatar': u'ad81b86bba0b59cc9e3d4d2896d67ca1',
                            u'bounces': {}}
                    }
                },
                u'grp1': {
                    u'description': u'The group 1',
                    u'domains': [],
                    u'members': {
                        u'DgQIBFsIGwElFQQHGhEWSwUOGA--': {
                            u'name': u'Jane Doe',
                            u'gravatar': u'98685715b08980dac8b2379097c332f4',
                            u'bounces': {
                                'end-date': '2016-01-01'}},
                        u'DgoOD1sIGwElFQQHGhEWSwUOGA--': {
                            u'name': u'John Doe',
                            u'gravatar': u'46d19d53d565a1c3dd2f322f7b76c449',
                            u'bounces': {}}
                    }
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
            response = self.app.get('/api/v1/groups/?prefix=grp2')
            assert response.status_int == 200
            expected_ret = {
                u'grp2': {
                    u'description': u'The group 2',
                    u'domains': [],
                    u'members': {
                        u'DgoOD1sIGwElFQQHGhEWSwUOGA--': {
                            u'name': u'John Doe',
                            u'gravatar': u'46d19d53d565a1c3dd2f322f7b76c449',
                            u'bounces': {}},
                        u'VFVWUVhcRFRV': {
                            u'name': u'Ampanman',
                            u'gravatar': u'ad81b86bba0b59cc9e3d4d2896d67ca1',
                            u'bounces': {}}
                    }
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
            '/api/v1/users/1', headers=headers, status="*")
        self.assertEqual(response.status_int, 404)

        # Push user details
        data = {
            'uid': '1',
            'name': 'saboten',
            'default-email': 'saboten@domain1',
            'emails': [
                {'email': 'saboten@domain1',
                 'groups': [
                     {'group': 'ugroup2',
                      'start-date': '2016-01-01',
                      'end-date': '2016-01-09'}
                 ]}
            ]}
        response = self.app.put_json(
            '/api/v1/users/1', data, headers=headers, status="*")
        self.assertEqual(response.status_int, 201)

        # Get User details
        response = self.app.get(
            '/api/v1/users/1', headers=headers, status="*")
        self.assertEqual(response.status_int, 200)
        self.assertDictEqual(response.json, data)

        # Update user details
        data['name'] = 'sabosan'
        response = self.app.post_json(
            '/api/v1/users/1', data, headers=headers, status="*")
        self.assertEqual(response.status_int, 200)

        # Get User details
        response = self.app.get(
            '/api/v1/users/1', headers=headers, status="*")
        self.assertEqual(response.status_int, 200)
        self.assertDictEqual(response.json, data)

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
            'emails': []}
        headers = {
            'REMOTE_USER': 'admin',
            'ADMIN_TOKEN': '12345'}
        self.app.put_json(
            '/api/v1/users/saboten', data, headers=headers, status="*")
        headers = {'REMOTE_USER': 'saboten'}
        response = self.app.get(
            '/api/v1/users/saboten', headers=headers, status="*")
        self.assertEqual(response.status_int, 200)
        self.assertDictEqual(response.json, data)
        data['default-email'] = 'saboten@domain2'
        response = self.app.post_json(
            '/api/v1/users/saboten', data, headers=headers, status="*")
        self.assertEqual(response.status_int, 200)
        headers = {'REMOTE_USER': 'tokin'}
        response = self.app.get(
            '/api/v1/users/saboten', headers=headers, status="*")
        self.assertEqual(response.status_int, 401)
        data['default-email'] = 'saboten@domain1'
        response = self.app.post_json(
            '/api/v1/users/saboten', data, headers=headers, status="*")
        self.assertEqual(response.status_int, 401)


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
        with patch.object(root.Projects, 'get_projects') as m:
            root.histo.indexname = 'repoxplorertest'
            m.return_value = self.projects
            response = self.app.get('/api/v1/histo/authors?pid=test')
        assert response.status_int == 200
        self.assertEqual(response.json[0]['value'], 2)
        self.assertEqual(response.json[0]['date'], '2014-09-11')
        self.assertIn('n.suke@joker.org', response.json[0]['authors_email'])
        self.assertIn('j.paul@joker.org', response.json[0]['authors_email'])

        with patch.object(root.Projects, 'get_projects') as m:
            root.histo.indexname = 'repoxplorertest'
            m.return_value = self.projects
            response = self.app.get(
                '/api/v1/histo/authors?pid=unknown', status="*")
        assert response.status_int == 404

    def test_get_commits_histo(self):
        with patch.object(root.Projects, 'get_projects') as m:
            root.histo.indexname = 'repoxplorertest'
            m.return_value = self.projects
            response = self.app.get('/api/v1/histo/commits?pid=test')
        assert response.status_int == 200
        self.assertListEqual(
            response.json,
            [{u'date': u'2014-09-11', u'value': 2}])


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
        with patch.object(root.Projects, 'get_projects') as m:
            root.infos.indexname = 'repoxplorertest'
            m.return_value = self.projects
            response = self.app.get('/api/v1/infos/infos?pid=test')
        assert response.status_int == 200
        expected = {
            'first': 1410456005,
            'last': 1410456005,
            'commits_amount': 2,
            'line_modifieds_amount': 20,
            'duration': 0,
            'ttl_average': 0
        }
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
        with patch.object(root.Projects, 'get_projects') as m:
            m.return_value = self.projects
            expected = {
                'version': version.get_version(),
                'projects': 1,
                'repos': 1,
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
        with patch.object(root.Projects, 'get_projects') as m:
            m.return_value = self.projects
            response = self.app.get('/api/v1/projects/projects')
            assert response.status_int == 200
            self.assertIn('test', response.json['projects'])


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

    def test_get_tops_authors(self):
        with patch.object(root.Projects, 'get_projects') as m:
            m.return_value = self.projects
            root.tops.indexname = 'repoxplorertest'
            response = self.app.get('/api/v1/tops/authors?pid=test')
            assert response.status_int == 200
            self.assertEqual(len(response.json['authors_lchanged']), 2)
            self.assertEqual(len(response.json['authors_commits']), 2)

    def test_get_tops_projects(self):
        with patch.object(root.Projects, 'get_projects') as m:
            m.return_value = self.projects
            root.tops.indexname = 'repoxplorertest'
            response = self.app.get('/api/v1/tops/projects?pid=test')
            expected = {
                'contributed_projects': ['test'],
                'sorted_contributed_repos_lchanged': [['test', 20]],
                'sorted_contributed_repos': [['test', 2]],
                'contributed_repos': {
                    'https://github.com/nakata/monkey.git:monkey:master': 2}
            }
            assert response.status_int == 200
            self.assertDictEqual(response.json, expected)


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
        response = self.app.get('/api/v1/search/search_authors?query=marc')
        cid = utils.encrypt(xorkey, 'j.marc@joker2.org')
        expected = {
            cid: {u'name': 'Jean Marc',
                  u'gravatar': u'185968ce180f4118a5334f0d2fdb5cbf'}}
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
        with patch.object(root.Projects, 'get_projects') as m:
            m.return_value = self.projects
            root.metadata.indexname = 'repoxplorertest'
            response = self.app.get('/api/v1/metadata/metadata?pid=test')
            assert response.status_int == 200
            self.assertDictEqual(
                response.json,
                {u'implement': 2, u'close-bug': 1})
            response = self.app.get(
                '/api/v1/metadata/metadata?key=implement&pid=test')
            assert response.status_int == 200
            self.assertIn('feature 35', response.json)
            self.assertIn('feature 36', response.json)
            self.assertEqual(len(response.json), 2)


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
        with patch.object(root.Projects, 'get_projects') as m:
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

    def test_get_commits(self):
        with patch.object(root.Projects, 'get_projects') as m:
            root.commits.indexname = 'repoxplorertest'
            m.return_value = self.projects

            response = self.app.get('/api/v1/commits/commits?pid=test')
            assert response.status_int == 200
            self.assertEqual(response.json[2][0]['author_name'],
                             'Nakata Daisuke')

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
            self.assertEqual(response.json[1], 2)

            response = self.app.get(
                '/api/v1/commits/commits?pid=test&'
                'inc_merge_commit=on')
            assert response.status_int == 200
            self.assertEqual(response.json[1], 3)
