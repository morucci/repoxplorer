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


import os
import yaml
import shutil
import tempfile
from mock import patch
from jsonschema import validate
from unittest import TestCase

from repoxplorer.index import contributors
from repoxplorer.index import yamlbackend
from repoxplorer.index import users
from repoxplorer import index


class TestContributors(TestCase):

    def setUp(self):
        self.dbs = []
        self.maxDiff = None

    def tearDown(self):
        for db in self.dbs:
            if os.path.isdir(db):
                shutil.rmtree(db)

    def create_db(self, files):
        db = tempfile.mkdtemp()
        self.dbs.append(db)
        for filename, content in files.items():
            open(os.path.join(db, filename), 'w+').write(content)
        return db

    def test_contributors_schema(self):
        validate(yaml.load(contributors.contributors_example,
                           Loader=yamlbackend.NoDatesSafeLoader),
                 yaml.load(contributors.contributors_schema))

    def test_groups_schema(self):
        validate(yaml.load(contributors.groups_example,
                           Loader=yamlbackend.NoDatesSafeLoader),
                 yaml.load(contributors.groups_schema))

    def test_contributors_get(self):
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
        index.conf['db_default_file'] = os.path.join(db,
                                                     'default.yaml')
        p = contributors.Contributors(db_path=db)
        ret = p._get_idents()
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
                                 'begin-date': 1451606400.0},
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
                                 'end-date': 1452297600.0,
                                 'begin-date': 1451606400.0
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
                                 'end-date': 1578528000.0,
                                 'begin-date': 1262304000.0
                             }
                         }
                     }
                 }}
             })

    def test_contributors_validate(self):
        f1 = """
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
            end-date: 2016-01-09
          acme-11:
          acme-12:
      jodoe@domain.com:
        groups: {}
  1234-1235:
    name: Jane Doe
    default-email: jadoe@domain.com
    emails:
      jane.doe@domain.com: {}
      jadoe@domain.com: {}

groups:
  acme-10:
    description: The group 10 of acme
    emails: {}
  acme-11:
    description: The group 11 of acme
    emails: {}
  acme-12:
    description: The group 12 of acme
    emails: {}
"""
        f2 = """
---
identities:
  1234-1236:
    name: John Doe
    default-email: john.doe@domain.com
    emails:
      john.doe@domain.com:
        groups:
          acme-10:
            begin-date: 2016-01-01
            end-date: 2016-01-09
          acme-11:
          acme-12:
      jodoe@domain.com:
        groups: {}
  1234-1237:
    name: Jane Doe
    default-email: jadoe@domain.com
    emails:
      jane.doe@domain.com: {}
      jadoe@domain.com: {}
"""

        files = {'f1.yaml': f1, 'f2.yaml': f2}
        db = self.create_db(files)
        index.conf['db_default_file'] = None
        p = contributors.Contributors(db_path=db)
        validation_logs = p._validate_idents()
        self.assertEqual(len(validation_logs), 0)

        f3 = """
---
identities:
  1234-1238:
    name: John Doe
    default-email: john.doe@domain.com
    emails:
      isthisanemail?
"""

        files = {'f1.yaml': f1, 'f2.yaml': f2, 'f3.yaml': f3}
        db = self.create_db(files)
        index.conf['db_default_file'] = None
        p = contributors.Contributors(db_path=db)
        validation_logs = p._validate_idents()
        self.assertEqual(validation_logs[0],
                         "'isthisanemail?' is not of type 'object'")
        self.assertEqual(len(validation_logs), 1)

        f3 = """
---
identities:
  1234-1237:
    name: John Doe
    default-email: jodoe@domain.com
    emails:
      jodoe@domain.com:
        groups: {}
"""

        files = {'f1.yaml': f1, 'f2.yaml': f2, 'f3.yaml': f3}
        db = self.create_db(files)
        index.conf['db_default_file'] = None
        p = contributors.Contributors(db_path=db)
        validation_logs = p._validate_idents()
        self.assertEqual(validation_logs[0],
                         "Identity IDs [1234-1237,] are duplicated")
        self.assertEqual(len(validation_logs), 1)

        f3 = """
---
identities:
  1234-1238:
    name: John Doe
    default-email: jodoe@domain.com
    emails:
      jdoe@domain.com:
        groups: {}
"""

        files = {'f1.yaml': f1, 'f2.yaml': f2, 'f3.yaml': f3}
        db = self.create_db(files)
        index.conf['db_default_file'] = None
        p = contributors.Contributors(db_path=db)
        validation_logs = p._validate_idents()
        self.assertEqual(validation_logs[0],
                         "Identity 1234-1238 default an unknown default-email")
        self.assertEqual(len(validation_logs), 1)

    def test_groups_validate(self):
        f1 = """
---
groups:
  acme-10:
    description: The group 10 of acme
    domains:
      - dom1.org
      - dom2.org
    emails:
      test@acme.com:
        begin-date: 2016-01-01
        end-date: 2016-01-09
      test2@acme.com:
"""
        f2 = """
---
groups:
  acme-11:
    description: The group 11 of acme
    emails:
      test@acme.com:
      test2@acme.com:
      test3@acme.com:
"""

        files = {'f1.yaml': f1, 'f2.yaml': f2}
        db = self.create_db(files)
        index.conf['db_default_file'] = None
        p = contributors.Contributors(db_path=db)
        validation_logs = p._validate_groups()
        self.assertEqual(len(validation_logs), 0)

        f3 = """
---
groups:
  acme-12:
    description: The group 12 of acme
    emails: wrong format
"""
        files = {'f1.yaml': f1, 'f2.yaml': f2, 'f3.yaml': f3}
        db = self.create_db(files)
        index.conf['db_default_file'] = None
        p = contributors.Contributors(db_path=db)
        validation_logs = p._validate_groups()
        self.assertEqual(validation_logs[0],
                         "'wrong format' is not of type 'object'")
        self.assertEqual(len(validation_logs), 1)

        f3 = """
---
groups:
  acme-11:
    description: The group 11 of acme
    emails:
      test@acme.com:
      test2@acme.com:
      test3@acme.com:
"""
        files = {'f1.yaml': f1, 'f2.yaml': f2, 'f3.yaml': f3}
        db = self.create_db(files)
        index.conf['db_default_file'] = None
        p = contributors.Contributors(db_path=db)
        validation_logs = p._validate_groups()
        self.assertEqual(validation_logs[0],
                         "Group IDs [acme-11,] are duplicated")
        self.assertEqual(len(validation_logs), 1)

    def test_groups_get(self):
        contributors.user_endpoint_active = False
        f1 = """
---
groups:
  acme-10:
    description: The group 10 of acme
    emails:
      test@acme.com:
        begin-date: 2016-01-01
        end-date: 2016-01-09
      test2@acme.com:
"""
        default = """
---
groups:
  acme-10:
    description: The group 10 of acme
    emails:
      test@acme.com:
      test2@acme.com:
  acme-11:
    description: The group 11 of acme
    emails:
      test@acme.com:
      test2@acme.com:
      test3@acme.com:
    domains:
      - dom1.org
"""
        files = {'f1.yaml': f1, 'default.yaml': default}
        db = self.create_db(files)
        index.conf['db_default_file'] = os.path.join(db,
                                                     'default.yaml')
        p = contributors.Contributors(db_path=db)
        ret = p.get_groups()
        self.assertDictEqual(
            ret,
            {'acme-10': {
                'emails': {
                    'test@acme.com': {
                        'begin-date': 1451606400.0,
                        'end-date': 1452297600.0},
                    'test2@acme.com': None},
                'description': 'The group 10 of acme'},
             'acme-11': {
                 'emails': {
                     'test3@acme.com': None,
                     'test@acme.com': None,
                     'test2@acme.com': None},
                 'domains': ['dom1.org'],
                 'description': 'The group 11 of acme'}
             })

    def test_groups_get_enriched(self):
        contributors.user_endpoint_active = False
        f1 = """
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
            end-date: 2016-01-09
          acme-11:
          acme-12:
      jodoe@domain.com:
        groups: {}
  1234-1235:
    name: Jane Doe
    default-email: jadoe@domain.com
    emails:
      jane.doe@domain.com:
        groups:
          acme-10:
            begin-date: 2015-01-01
            end-date: 2015-01-09
      jadoe@domain.com:
        groups:
          acme-12:
            begin-date: 2015-01-01
            end-date: 2015-01-05

groups:
  acme-10:
    description: The group 10 of acme
    emails: {}
  acme-11:
    description: The group 11 of acme
    emails:
      ampanman@baikinman.com:
  acme-12:
    description: The group 12 of acme
    emails:
      ampanman@baikinman.com:
    domains:
      - acme12.org
"""
        files = {'f1.yaml': f1}
        db = self.create_db(files)
        index.conf['db_default_file'] = None
        p = contributors.Contributors(db_path=db)
        ret = p.get_groups()
        expected_ret = {
            'acme-12': {
                'description': 'The group 12 of acme',
                'domains': ['acme12.org'],
                'emails': {
                    'john.doe@domain.com': None,
                    'jadoe@domain.com': {
                        'end-date': 1420416000.0,
                        'begin-date': 1420070400.0},
                    'ampanman@baikinman.com': None}},
            'acme-11': {
                'description': 'The group 11 of acme',
                'emails': {
                    'john.doe@domain.com': None,
                    'ampanman@baikinman.com': None}},
            'acme-10': {
                'description': 'The group 10 of acme',
                'emails': {
                    'john.doe@domain.com': {
                        'end-date': 1452297600.0,
                        'begin-date': 1451606400.0},
                    'jane.doe@domain.com': {
                        'end-date': 1420761600.0,
                        'begin-date': 1420070400.0}}}}
        self.assertDictEqual(ret, expected_ret)

    def test_get_idents_by_emails(self):
        contributors.user_endpoint_active = False
        with patch.object(index.YAMLBackend, 'load_db'):
            with patch.object(contributors.Contributors, '_get_idents') as gi:
                gi.return_value = {
                    '1234-1235': {
                        'name': 'Jane Doe',
                        'emails': {
                            'jane.doe@domain.com': {},
                            'jadoe@domain.com': {}}}}
                c = contributors.Contributors(db_path="db_path")
                ret = c.get_idents_by_emails('jadoe@domain.com')
                self.assertTrue(len(ret), 1)
                self.assertDictEqual(
                    ret['1234-1235'],
                    {'name': 'Jane Doe',
                     'emails': {'jadoe@domain.com': {},
                                'jane.doe@domain.com': {}}})
                ret = c.get_idents_by_emails('shimajiro@domain.com')
                self.assertDictEqual(
                    ret['shimajiro@domain.com'],
                    {'name': None,
                     'default-email': 'shimajiro@domain.com',
                     'emails': {'shimajiro@domain.com': {}}})
                gi.return_value = {
                    '1234-1235': {
                        'name': 'Jane Doe',
                        'emails': {
                            'jane.doe@domain.com': {},
                            'jadoe@domain.com': {}}},
                    '1234-1236': {
                        'name': 'John Doe',
                        'emails': {
                            'johndoe@domain.com': {}}},
                    '1234-1237': {
                        'name': 'Ampanman',
                        'emails': {
                            'ampanman@domain.com': {}}},
                }
                ret = c.get_idents_by_emails(
                    ['ampanman@domain.com', 'johndoe@domain.com'])
                self.assertDictEqual(
                    ret['1234-1237'],
                    {'name': 'Ampanman',
                     'emails': {'ampanman@domain.com': {}}})
                self.assertDictEqual(
                    ret['1234-1236'],
                    {'name': 'John Doe',
                     'emails': {'johndoe@domain.com': {}}})
                self.assertEqual(len(ret), 2)

    def test_get_ident_by_id(self):
        contributors.user_endpoint_active = False
        with patch.object(index.YAMLBackend, 'load_db'):
            with patch.object(contributors.Contributors, '_get_idents') as gi:
                gi.return_value = {
                    '1234-1235': {
                        'name': 'Jane Doe',
                        'emails': {
                            'jane.doe@domain.com': {},
                            'jadoe@domain.com': {}}}}
                c = contributors.Contributors(db_path="db_path")

                cid, cdata = c.get_ident_by_id('8888-8888')
                self.assertEqual(cid, '8888-8888')
                self.assertEqual(cdata, None)

                cid, cdata = c.get_ident_by_id('1234-1235')
                self.assertEqual(cid, '1234-1235')
                self.assertEqual(cdata['name'], 'Jane Doe')

    def test_get_group_by_id(self):
        contributors.user_endpoint_active = False
        with patch.object(index.YAMLBackend, 'load_db'):
            with patch.object(contributors.Contributors, 'get_groups') as gg:
                gg.return_value = {
                    'acme-11': {
                        'description': 'The group 11 of acme',
                        'emails': {
                            'john.doe@domain.com': None,
                            'ampanman@baikinman.com': None}}}
                c = contributors.Contributors(db_path="db_path")

                gid, gdata = c.get_group_by_id('zzz')
                self.assertEqual(gid, 'zzz')
                self.assertEqual(gdata, None)

                gid, gdata = c.get_group_by_id('acme-11')
                self.assertEqual(gid, 'acme-11')
                self.assertEqual(gdata['description'],
                                 'The group 11 of acme')

    def test_get_idents_by_emails_with_user_backend(self):
        contributors.user_endpoint_active = True
        with patch.object(index.YAMLBackend, 'load_db'):
            with patch.object(contributors.Contributors, '_get_idents'):
                with patch.object(users.Users,
                                  'get_idents_by_emails') as egi:
                    egi.return_value = [
                        {'name': 'John Doe',
                         'default-email': 'jdoe@domain.com',
                         'emails': [
                            {'email': 'jdoe@domain.com'},
                            {'email': 'john.doe@domain.com',
                             'groups': [{'group': 'barbican-ptl'}]}
                         ],
                         'uid': 'johndoe123'},
                    ]

                    c = contributors.Contributors(db_path="db_path")

                    ret = c.get_idents_by_emails('jdoe@domain.com')
                    self.assertDictEqual(
                       ret['johndoe123'],
                       {'name': 'John Doe',
                        'default-email': 'jdoe@domain.com',
                        'emails': {'jdoe@domain.com': {'groups': {}},
                                   'john.doe@domain.com': {
                                       'groups': {
                                           'barbican-ptl': {}
                                       }}
                                   }
                        })

    def test_get_ident_by_id_with_user_backend(self):
        contributors.user_endpoint_active = True
        with patch.object(index.YAMLBackend, 'load_db'):
            with patch.object(contributors.Contributors, '_get_idents'):
                with patch.object(users.Users,
                                  'get_ident_by_id') as egi:
                    egi.return_value = {
                        'name': 'John Doe',
                        'default-email': 'jdoe@domain.com',
                        'emails': [
                            {'email': 'jdoe@domain.com'},
                            {'email': 'john.doe@domain.com',
                             'groups': [{'group': 'barbican-ptl'}]}
                         ],
                        'uid': 'johndoe123'}

                    c = contributors.Contributors(db_path="db_path")

                    id, ident = c.get_ident_by_id('johndoe123')
                    self.assertEqual(ident['name'], 'John Doe')
                    self.assertEqual(id, 'johndoe123')

    def test_get_group_by_id_with_users_backend(self):
        contributors.user_endpoint_active = True
        with patch.object(index.YAMLBackend, 'load_db'):
            with patch.object(users.Users,
                              'get_idents_in_group') as egi:
                egi.return_value = [
                    {'name': 'John Doe',
                     'default-email': 'jdoe@domain.com',
                     'emails': [
                        {'email': 'jdoe@domain.com'},
                        {'email': 'john.doe@domain.com',
                         'groups': [{'group': 'barbican-ptl'}]}
                     ],
                     'uid': 'johndoe123'},
                ]

                c = contributors.Contributors(db_path="db_path")
                c.groups = {
                    'barbican-ptl': {
                        'description': 'The barbican-ptl group',
                        'emails': {}},
                    'barbican-core': {
                        'description': 'The barbican-core group',
                        'emails': {}}
                }

                gid, gdata = c.get_group_by_id('barbican-ptl')
                self.assertDictEqual(
                    gdata,
                    {'description': 'The barbican-ptl group',
                     'emails': {'john.doe@domain.com': {}}})
                self.assertEqual(gid, 'barbican-ptl')

                gid, gdata = c.get_group_by_id('barbican-core')
                self.assertDictEqual(
                    gdata,
                    {'description': 'The barbican-core group',
                     'emails': {}})
                self.assertEqual(gid, 'barbican-core')
