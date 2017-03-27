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


class TestContributors(TestCase):

    def setUp(self):
        self.dbs = []

    def tearDown(self):
        for db in self.dbs:
            if os.path.isdir(db):
                shutil.rmtree(db)

    def create_db(self, files):
        db = tempfile.mkdtemp()
        self.dbs.append(db)
        for filename, content in files.items():
            file(os.path.join(db, filename), 'w+').write(content)
        return db

    def test_contributors_schema(self):
        validate(yaml.load(contributors.contributors_example),
                 yaml.load(contributors.contributors_schema))

    def test_groups_schema(self):
        validate(yaml.load(contributors.groups_example),
                 yaml.load(contributors.groups_schema))

    def test_contributors_get(self):
        f1 = """
---
identities:
  1234-1233:
    name: Amperman
    emails:
      ampanman@baikinman.io:
        groups:
          amp:
            begin-date: 2010/01/01
            end-date: 2020/09/01
"""
        f2 = """
---
identities:
  1234-1236:
    name: Bill Doe
    emails:
      bill.doe@domain.com:
        groups:
          acme-12:
            begin-date: 2016/01/01
            end-date: 2016/09/01
"""

        default = """
---
identities:
  1234-1234:
    name: John Doe
    emails:
      john.doe@domain.com:
        groups:
          acme-10:
            begin-date: 2016/01/01
            end-date: 2016/09/01
          acme-11:
          acme-12:
      jodoe@domain.com:
        groups: {}
  1234-1235:
    name: Jane Doe
    emails:
      jane.doe@domain.com: {}
      jadoe@domain.com: {}
  1234-1236:
    name: Bill Doe
    emails:
      bill.doe@domain.com: {}
      bdoe@domain.com: {}
"""
        files = {'f1.yaml': f1, 'f2.yaml': f2, 'default.yaml': default}
        db = self.create_db(files)
        contributors.conf['db_default_file'] = os.path.join(db,
                                                            'default.yaml')
        p = contributors.Contributors(db_path=db)
        ret = p.get_idents()
        self.assertDictEqual(
            ret,
            {'1234-1235': {
                'name': 'Jane Doe',
                'emails': {
                    'jane.doe@domain.com': {},
                    'jadoe@domain.com': {}
                }},
             '1234-1234': {
                 'name': 'John Doe',
                 'emails': {
                     'john.doe@domain.com': {
                         'groups': {
                             'acme-12': None,
                             'acme-10': {
                                 'end-date': '2016/09/01',
                                 'begin-date': '2016/01/01'},
                             'acme-11': None
                         }},
                     'jodoe@domain.com': {
                         'groups': {}
                     }
                 }},
             '1234-1236': {
                 'name': 'Bill Doe',
                 'emails': {
                     'bill.doe@domain.com': {
                         'groups': {
                             'acme-12': {
                                 'end-date': '2016/09/01',
                                 'begin-date': '2016/01/01'
                             }
                         }
                     }
                 }},
             '1234-1233': {
                 'name': 'Amperman',
                 'emails': {
                     'ampanman@baikinman.io': {
                         'groups': {
                             'amp': {
                                 'end-date': '2020/09/01',
                                 'begin-date': '2010/01/01'
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
    emails:
      john.doe@domain.com:
        groups:
          acme-10:
            begin-date: 2016/01/01
            end-date: 2016/09/01
          acme-11:
          acme-12:
      jodoe@domain.com:
        groups: {}
  1234-1235:
    name: Jane Doe
    emails:
      jane.doe@domain.com: {}
      jadoe@domain.com: {}
"""
        f2 = """
---
identities:
  1234-1236:
    name: John Doe
    emails:
      john.doe@domain.com:
        groups:
          acme-10:
            begin-date: 2016/01/01
            end-date: 2016/09/01
          acme-11:
          acme-12:
      jodoe@domain.com:
        groups: {}
  1234-1237:
    name: Jane Doe
    emails:
      jane.doe@domain.com: {}
      jadoe@domain.com: {}
"""

        files = {'f1.yaml': f1, 'f2.yaml': f2}
        db = self.create_db(files)
        contributors.conf['db_default_file'] = None
        p = contributors.Contributors(db_path=db)
        validation_logs = p.validate_idents()
        self.assertEqual(len(validation_logs), 0)

        f3 = """
---
identities:
  1234-1238:
    name: John Doe
    emails:
      isthisanemail?
"""

        files = {'f1.yaml': f1, 'f2.yaml': f2, 'f3.yaml': f3}
        db = self.create_db(files)
        contributors.conf['db_default_file'] = None
        p = contributors.Contributors(db_path=db)
        validation_logs = p.validate_idents()
        self.assertEqual(validation_logs[0],
                         "'isthisanemail?' is not of type 'object'")
        self.assertEqual(len(validation_logs), 1)

        f3 = """
---
identities:
  1234-1237:
    name: John Doe
    emails:
      jodoe@domain.com:
        groups: {}
"""

        files = {'f1.yaml': f1, 'f2.yaml': f2, 'f3.yaml': f3}
        db = self.create_db(files)
        contributors.conf['db_default_file'] = None
        p = contributors.Contributors(db_path=db)
        validation_logs = p.validate_idents()
        self.assertEqual(validation_logs[0],
                         "Identity IDs [1234-1237,] are duplicated")
        self.assertEqual(len(validation_logs), 1)

    def test_groups_validate(self):
        f1 = """
---
groups:
  acme-10:
    description: The group 10 of acme
    emails:
      test@acme.com:
        begin-date: 2016/01/01
        end-date: 2016/09/01
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
        contributors.conf['db_default_file'] = None
        p = contributors.Contributors(db_path=db)
        validation_logs = p.validate_groups()
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
        contributors.conf['db_default_file'] = None
        p = contributors.Contributors(db_path=db)
        validation_logs = p.validate_groups()
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
        contributors.conf['db_default_file'] = None
        p = contributors.Contributors(db_path=db)
        validation_logs = p.validate_groups()
        self.assertEqual(validation_logs[0],
                         "Group IDs [acme-11,] are duplicated")
        self.assertEqual(len(validation_logs), 1)

    def test_groups_get(self):
        f1 = """
---
groups:
  acme-10:
    description: The group 10 of acme
    emails:
      test@acme.com:
        begin-date: 2016/01/01
        end-date: 2016/09/01
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
"""
        files = {'f1.yaml': f1, 'default.yaml': default}
        db = self.create_db(files)
        contributors.conf['db_default_file'] = os.path.join(db,
                                                            'default.yaml')
        p = contributors.Contributors(db_path=db)
        ret = p.get_groups()
        self.assertDictEqual(
            ret,
            {'acme-10': {
                'emails': {
                    'test@acme.com': {
                        'begin-date': '2016/01/01',
                        'end-date': '2016/09/01'},
                    'test2@acme.com': None},
                'description': 'The group 10 of acme'},
             'acme-11': {
                 'emails': {
                     'test3@acme.com': None,
                     'test@acme.com': None,
                     'test2@acme.com': None},
                 'description': 'The group 11 of acme'}
             })

    def test_get_ident_by_email(self):
        with patch.object(contributors.YAMLBackend, 'load_db'):
            with patch.object(contributors.Contributors, 'get_idents') as gi:
                gi.return_value = {
                    '1234-1235': {
                        'name': 'Jane Doe',
                        'emails': {
                            'jane.doe@domain.com': {},
                            'jadoe@domain.com': {}}}}
                c = contributors.Contributors(db_path="db_path")
                cid, cdata = c.get_ident_by_email('jadoe@domain.com')
                self.assertDictEqual(
                    cdata,
                    {'name': 'Jane Doe',
                     'emails': {'jadoe@domain.com': {},
                                'jane.doe@domain.com': {}}})
                self.assertEqual(cid, '1234-1235')
                cid, cdata = c.get_ident_by_email('shimajiro@domain.com')
                self.assertDictEqual(
                    cdata,
                    {'name': None,
                     'emails': {'shimajiro@domain.com': {}}})
                self.assertEqual(cid, None)
