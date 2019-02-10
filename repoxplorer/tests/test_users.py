# Copyright 2017, Fabien Boucher
# Copyright 2019, Fabien Boucher
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

import os
import copy
import shutil
import tempfile

from unittest import TestCase

from repoxplorer import index
from repoxplorer.index.users import Users


class TestUsers(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.con = index.Connector(index='repoxplorertest',
                                  index_suffix='users')
        cls.c = Users(connector=cls.con)
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
        self.dbs = []
        self.maxDiff = None

    def tearDown(self):
        self.c.delete_all()
        for db in self.dbs:
            if os.path.isdir(db):
                shutil.rmtree(db)

    def create_db(self, files):
        db = tempfile.mkdtemp()
        self.dbs.append(db)
        for filename, content in files.items():
            open(os.path.join(db, filename), 'w+').write(content)
        return db

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

        ret = self.c._get_idents_by_emails('saboten@domain3')
        self.assertDictEqual(ret[0], u_user)

        ret = self.c._get_idents_by_emails(
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

    def test_user_load_from_yaml(self):
        f1 = """
---
identities:
  1234-1233:
    name: Amperman
    default-email: ampanman@baikinman.io
    emails:
      ampanman@baikinman.io:
        groups:
          amp:
            begin-date: 2010-01-01
            end-date: 2020-01-09
"""
        f2 = """
---
identities:
  1234-1236:
    name: Bill Doe
    default-email: bill.doe@domain.com
    emails:
      bill.doe@domain.com:
        groups:
          acme-12:
            begin-date: 2016-01-01
            end-date: 2016-01-09
"""

        default = """
---
identities:
  1234-1234:
    name: John Doe
    default-email: john.doe@domain.com
    emails:
      john.doe@domain.com:
        groups:
          acme-10:
            begin-date: 2016-01-01
          acme-11:
          acme-12:
      jodoe@domain.com:
        groups: {}
  1234-1235:
    name: Jane Doe
    default-email: jane.doe@domain.com
    emails:
      jane.doe@domain.com: {}
      jadoe@domain.com: {}
  1234-1236:
    name: Bill Doe
    default-email: bill.doe@domain.com
    emails:
      bill.doe@domain.com: {}
      bdoe@domain.com: {}
"""
        files = {'f1.yaml': f1, 'f2.yaml': f2, 'default.yaml': default}
        db = self.create_db(files)
        index.conf['db_default_file'] = os.path.join(
            db, 'default.yaml')
        c = Users(db_path=db, connector=self.con, dump_yaml_in_index=True)
        ret = c.get_idents()
        print(ret)
        self.assertDictEqual(
            ret,
            {'1234-1235': {
                'name': 'Jane Doe',
                'default-email': 'jane.doe@domain.com',
                'emails': {
                    'jane.doe@domain.com': {},
                    'jadoe@domain.com': {}
                }},
             '1234-1234': {
                 'name': 'John Doe',
                 'default-email': 'john.doe@domain.com',
                 'emails': {
                     'john.doe@domain.com': {
                         'groups': {
                             'acme-12': None,
                             'acme-10': {
                                 'end-date': None,
                                 'begin-date': 1451606400},
                             'acme-11': None
                         }},
                     'jodoe@domain.com': {
                         'groups': {}
                     }
                 }},
             '1234-1236': {
                 'name': 'Bill Doe',
                 'default-email': 'bill.doe@domain.com',
                 'emails': {
                     'bill.doe@domain.com': {
                         'groups': {
                             'acme-12': {
                                 'end-date': 1452297600,
                                 'begin-date': 1451606400
                             }
                         }
                     }
                 }},
             '1234-1233': {
                 'name': 'Amperman',
                 'default-email': 'ampanman@baikinman.io',
                 'emails': {
                     'ampanman@baikinman.io': {
                         'groups': {
                             'amp': {
                                 'end-date': 1578528000,
                                 'begin-date': 1262304000
                             }
                         }
                     }
                 }}
             })
