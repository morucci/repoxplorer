# Copyright 2017, Fabien Boucher
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
from unittest import TestCase

from repoxplorer import index
from repoxplorer.index.users import Users


class TestUsers(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.con = index.Connector(index='repoxplorertest',
                                  index_suffix='users')
        cls.c = Users(cls.con)
        cls.user = {
            'uid': '123',
            'name': 'saboten',
            'default-email': 'saboten@domain1',
            'emails': [
                {'email': 'saboten@domain1'},
                {'email': 'saboten@domain2',
                 'groups': [
                     {'group': 'ugroup1',
                      'begin-date': '2016-01-01',
                      'end-date': '2016-01-09'}],
                 }],
            'last_cnx': 1410456005}
        cls.user2 = {
            'uid': '124',
            'name': 'ampanman',
            'default-email': 'ampanman@domain1',
            'emails': [
                {'email': 'ampanman@domain1'}],
            'last_cnx': 1410456006}

    @classmethod
    def tearDownClass(cls):
        cls.con.ic.delete(index=cls.con.index)

    def setUp(self):
        # Be sure users are deleted
        self.c.delete(self.user['uid'])
        self.c.delete(self.user2['uid'])

    def tearDown(self):
        # Be sure users are deleted
        self.c.delete(self.user['uid'])
        self.c.delete(self.user2['uid'])

    def test_user_crud(self):
        # Create and get a user
        self.c.create(self.user)
        ret = self.c.get(self.user['uid'])
        self.assertDictEqual(ret, self.user)
        self.c.create(self.user2)
        ret = self.c.get(self.user2['uid'])
        self.assertDictEqual(ret, self.user2)

        # Update and get a user
        u_user = copy.deepcopy(self.user)
        u_user['emails'] = [{'email': 'saboten@domain3',
                             'groups': [
                                 {'group': 'ugroup2'}
                             ]}]
        u_user['name'] = 'Cactus Saboten Junior'
        self.c.update(u_user)
        ret = self.c.get(self.user['uid'])
        self.assertDictEqual(ret, u_user)

        ret = self.c.get_idents_by_emails('saboten@domain3')
        self.assertDictEqual(ret[0], u_user)

        ret = self.c.get_idents_by_emails(
            ['saboten@domain3', 'ampanman@domain1'])
        self.assertEqual(len(ret), 2)
        self.assertIn('ampanman', [r['name'] for r in ret])
        self.assertIn('Cactus Saboten Junior', [r['name'] for r in ret])

        idents_list = self.c.get_idents_in_group('ugroup2')
        self.assertListEqual(
            idents_list,
            [{'uid': '123',
              'default-email': 'saboten@domain1',
              'name': 'Cactus Saboten Junior',
              'emails': [{
                  'groups': [{'group': 'ugroup2'}],
                  'email': 'saboten@domain3'}],
              'last_cnx': 1410456005}])

        # Delete and get a user
        self.c.delete(self.user['uid'])
        self.assertEqual(
            self.c.get(self.user['uid']), None)
