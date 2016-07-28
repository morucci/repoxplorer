import os
import tempfile
from unittest import TestCase

from repoxplorer.index.projects import Projects


class TestProjects(TestCase):

    def setUp(self):
        self.to_delete = []

    def tearDown(self):
        map(lambda x: os.unlink(x),
            self.to_delete)

    def create_projects_yaml(self, data):
        d, path = tempfile.mkstemp()
        os.write(d, data)
        os.close(d)
        self.to_delete.append(path)
        return path

    def test_projects_data_init(self):
        projects_yaml = """
---
- templates:
   - name: default
     branch: master
     uri: http://gb.com/ok/%(name)s
     gitweb: http://gb.com/ok/%(name)s/commit/%%(sha)s

- projects:
   - Barbican:
      - name: barbican
        template: default
      - name: python-barbicanclient
        template: default
"""
        path = self.create_projects_yaml(projects_yaml)
        p = Projects(projects_file_path=path)
        self.assertIn("Barbican", p.projects)
        self.assertEqual(len(p.projects['Barbican']), 2)

        projects_yaml = """
---
- templates:
   - name: default
     branch: master
     uri: http://gb.com/ok/%(name)s
     gitweb: http://gb.com/ok/%(name)s/commit/%%(sha)s

- projects:
   - Barbican:
      - name: barbican
        template: default
        uri: http://test.com/ok/%(name)s
        gitweb: http://test.com/ok/%(name)s/commit/%%(sha)s
      - name: python-barbicanclient
        template: default
"""
        path = self.create_projects_yaml(projects_yaml)
        p = Projects(projects_file_path=path)
        self.assertIn("Barbican", p.projects)
        self.assertEqual(len(p.projects['Barbican']), 2)
        mp1 = [m for m in p.get_projects()['Barbican']
               if m['name'] == 'barbican'][0]
        mp2 = [m for m in p.get_projects()['Barbican']
               if m['name'] == 'python-barbicanclient'][0]
        self.assertEqual(mp1['uri'], 'http://test.com/ok/barbican')
        self.assertEqual(mp2['uri'], 'http://gb.com/ok/python-barbicanclient')
