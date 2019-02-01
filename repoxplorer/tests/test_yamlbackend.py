# Copyright 2017, Red Hat
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
import shutil
import tempfile
from unittest import TestCase

from repoxplorer.index.yamlbackend import YAMLBackend


class TestYAMLBackend(TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        if os.path.isdir(self.db):
            shutil.rmtree(self.db)

    def create_db(self, files):
        self.db = tempfile.mkdtemp()
        for filename, content in files.items():
            open(os.path.join(self.db, filename), 'w+').write(content)

    def test_yamlbackend_load(self):
        f1 = """
---
key: value
"""
        f2 = """
---
key2: value2
"""
        files = {'f1.yaml': f1, 'f2.yaml': f2}
        self.create_db(files)
        backend = YAMLBackend(db_path=self.db)
        backend.load_db()
        default_data, data = backend.get_data()
        self.assertEqual(default_data, None)
        self.assertEqual(len(data), 2)

    def test_yamlbackend_load_with_default(self):
        f1 = """
---
key: value
"""
        f2 = """
---
key2: value2
"""
        files = {'default.yaml': f1, 'f2.yaml': f2}
        self.create_db(files)
        backend = YAMLBackend(
            db_path=self.db,
            db_default_file=os.path.join(self.db, 'default.yaml'))
        backend.load_db()
        default_data, data = backend.get_data()
        self.assertDictEqual(default_data, {'key': 'value'})
        self.assertEqual(len(data), 1)
        self.assertDictEqual(data[0], {'key2': 'value2'})
