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
from repoxplorer.index.users import Groups


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
                      'start-date': '01/01/2016',
                      'end-date': '09/01/2016'}],
                 }],
            'last_cnx': 1410456005}

    @classmethod
    def tearDownClass(cls):
        cls.con.ic.delete(index=cls.con.index)

    def test_user_crud(self):
        # Create and get a user
        self.c.create(self.user)
        ret = self.c.get(self.user['uid'])
        self.assertDictEqual(ret, self.user)

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

        ret = self.c.get_ident_by_email('saboten@domain3')
        self.assertDictEqual(ret, u_user)

        idents_list = self.c.get_idents_in_group('ugroup2')
        self.assertListEqual(
            idents_list,
            [{u'uid': u'123',
              u'default-email': u'saboten@domain1',
              u'name': u'Cactus Saboten Junior',
              u'emails': [{
                  u'groups': [{u'group': u'ugroup2'}],
                  u'email': u'saboten@domain3'}],
              u'last_cnx': 1410456005}])

        # Delete and get a user
        self.c.delete(self.user['uid'])
        self.assertEqual(
            self.c.get(self.user['uid']), None)


class TestGroups(TestCase):

    def setUp(self):
        self.con = index.Connector(index='repoxplorertest',
                                   index_suffix='users')
        self.c = Groups(self.con)
        self.cu = Users(self.con)
        self.user = {
            'uid': '234',
            'name': 'Cactus Saboten',
            'default-email': 'saboten@domain1',
            'emails': [
                {'email': 'saboten@domain1'},
                {'email': 'saboten@domain2',
                 'groups': [
                     {'group': 'ugroup1',
                      'start-date': '01/01/2016',
                      'end-date': '09/01/2016'}],
                 }],
            'last_cnx': 1410456005}
        self.cu.create(self.user)
        self.group = {
            'gid': 'ugroup1',
            'description': 'ugroup',
            'emails': [{'email': 'tokin@domain1'},
                       {'email': 'kokin@domain2',
                        'start-date': '01/01/2016',
                        'end-date': '09/01/2016'}]}

    def tearDown(self):
        self.con.ic.delete(index=self.con.index)

    def test_group_crud(self):
        # Create and get a group
        self.c.create(self.group)
        ret = self.c.get(self.group['gid'])
        expected = {
            u'description': u'ugroup',
            u'emails': [
                {u'email': u'tokin@domain1'},
                {u'start-date': u'01/01/2016',
                 u'end-date': u'09/01/2016',
                 u'email': u'kokin@domain2'},
                {u'start-date': u'01/01/2016',
                 u'end-date': u'09/01/2016',
                 'email': u'saboten@domain2'}],
            u'gid': u'ugroup1'}
        self.assertDictEqual(ret, expected)

        # Update and get a group
        u_group = copy.deepcopy(self.group)
        u_group['emails'] = [{'email': 'gokin@domain3'}]
        u_group['description'] = 'New group description'
        self.c.update(u_group)
        ret = self.c.get(self.group['gid'])
        expected = {
            u'description': u'New group description',
            u'emails': [
                {u'email': u'gokin@domain3'},
                {'email': u'saboten@domain2',
                 u'start-date': u'01/01/2016',
                 u'end-date': u'09/01/2016'}],
            u'gid': u'ugroup1'}
        self.assertDictEqual(ret, expected)

        # Delete and get a group
        self.c.delete(self.group['gid'])
        self.assertEqual(
            self.c.get(self.group['gid']), None)

    def test_group_get_all(self):
        # Create and get a group
        group1 = copy.deepcopy(self.group)
        group2 = copy.deepcopy(self.group)
        group2['gid'] = 'ugroup2'
        self.c.create(group1)
        self.c.create(group2)
        self.assertEqual(2, len(self.c.get_all()))
        self.c.delete(group1['gid'])
        self.c.delete(group2['gid'])
