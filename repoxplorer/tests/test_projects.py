import os
import yaml
import shutil
import tempfile
from jsonschema import validate
from unittest import TestCase

from repoxplorer.index import projects
from repoxplorer import index


class TestProjects(TestCase):

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
            file(os.path.join(db, filename), 'w+').write(content)
        return db

    def test_project_templates_schema(self):
        validate(yaml.load(projects.project_templates_example),
                 yaml.load(projects.project_templates_schema))

    def test_projects_schema(self):
        validate(yaml.load(projects.projects_example),
                 yaml.load(projects.projects_schema))

    def test_get_projects_raw(self):
        f1 = """
        project-templates:
          mytemplate:
            uri: https://bitbucket.com/%(name)s
            branches:
            - master
            gitweb: https://bitbucket.com/%(name)s/commit/%%(sha)s
            releases:
            - name: 1.0
              date: 12/20/2016
            - name: 2.0
              date: 12/31/2016

        projects:
          Barbican:
            openstack/barbican:
              template: mytemplate
            openstack/python-barbicanclient:
              template: mytemplate
          Swift:
            openstack/swift:
              template: default
            openstack/python-swiftclient:
              template: default
        """

        default = """
        project-templates:
          default:
            uri: https://github.com/%(name)s
            branches:
            - master
            - stable/newton
            - stable/ocata
            gitweb: https://github.com/openstack/%(name)s/commit/%%(sha)s
            tags:
            - openstack
            parsers:
            - .*(blueprint) ([^ .]+).*

        projects:
          Barbican:
            openstack/barbican:
              template: default
            openstack/python-barbicanclient:
              template: default
          Nova:
            openstack/nova:
              template: default
              paths:
              - tests/
            openstack/python-novaclient:
              template: default
        """
        files = {'f1.yaml': f1, 'default.yaml': default}
        db = self.create_db(files)
        index.conf['db_default_file'] = os.path.join(db,
                                                     'default.yaml')
        p = projects.Projects(db_path=db)
        ret = p.get_projects_raw()
        expected_ret = {
            'Nova': {
                'openstack/python-novaclient': {
                    'tags': ['openstack'],
                    'branches': ['master', 'stable/newton', 'stable/ocata'],
                    'parsers': ['.*(blueprint) ([^ .]+).*'],
                    'gitweb': 'https://github.com/openstack/openstack/'
                              'python-novaclient/commit/%(sha)s',
                    'releases': [],
                    'uri': 'https://github.com/openstack/python-novaclient'},
                'openstack/nova': {
                    'tags': ['openstack'],
                    'branches': ['master', 'stable/newton', 'stable/ocata'],
                    'parsers': ['.*(blueprint) ([^ .]+).*'],
                    'gitweb': 'https://github.com/openstack/openstack/'
                              'nova/commit/%(sha)s',
                    'releases': [],
                    'paths': ['tests/'],
                    'uri': 'https://github.com/openstack/nova'}},
            'Swift': {
                'openstack/swift': {
                    'tags': ['openstack'],
                    'branches': ['master', 'stable/newton', 'stable/ocata'],
                    'parsers': ['.*(blueprint) ([^ .]+).*'],
                    'gitweb': 'https://github.com/openstack/openstack/'
                              'swift/commit/%(sha)s',
                    'releases': [],
                    'uri': 'https://github.com/openstack/swift'},
                'openstack/python-swiftclient': {
                    'tags': ['openstack'],
                    'branches': ['master', 'stable/newton', 'stable/ocata'],
                    'parsers': ['.*(blueprint) ([^ .]+).*'],
                    'gitweb': 'https://github.com/openstack/openstack/'
                              'python-swiftclient/commit/%(sha)s',
                    'releases': [],
                    'uri': 'https://github.com/openstack/python-swiftclient'}},
            'Barbican': {
                'openstack/barbican': {
                    'branches': ['master'],
                    'parsers': [],
                    'gitweb': 'https://bitbucket.com/openstack/'
                              'barbican/commit/%(sha)s',
                    'uri': 'https://bitbucket.com/openstack/barbican',
                    'tags': [],
                    'releases': [
                        {'name': 1.0, 'date': 1482192000.0},
                        {'name': 2.0, 'date': 1483142400.0}]},
                'openstack/python-barbicanclient': {
                    'branches': ['master'],
                    'parsers': [],
                    'gitweb': 'https://bitbucket.com/openstack/'
                              'python-barbicanclient/commit/%(sha)s',
                    'uri': 'https://bitbucket.com/openstack/'
                           'python-barbicanclient',
                    'tags': [],
                    'releases': [
                        {'name': 1.0, 'date': 1482192000.0},
                        {'name': 2.0, 'date': 1483142400.0}]}}}
        self.assertDictEqual(expected_ret, ret)

    def test_projects_validate(self):
        f1 = """
        project-templates:
          default:
            uri: https://github.com/%(name)s
            branches:
            - master
            gitweb: https://github.com/openstack/%(name)s/commit/%%(sha)s
        """

        f2 = """
        projects:
          Barbican:
            openstack/barbican:
              template: mytemplate
        """
        files = {'f1.yaml': f1, 'f2.yaml': f2}
        db = self.create_db(files)
        index.conf['db_default_file'] = None
        p = projects.Projects(db_path=db)
        issues = p.validate()
        self.assertIn("Project ID 'Barbican' Repo ID 'openstack/barbican' "
                      "references an unknown template mytemplate",
                      issues)
        self.assertEqual(len(issues), 1)

        f1 = """
        project-templates:
          default:
            uri: https://github.com/%(name)s
            branches:
            - master
            gitweb: https://github.com/openstack/%(name)s/commit/%%(sha)s
            releases:
            - name: "1.0"
              date: wrong
        """

        files = {'f1.yaml': f1}
        db = self.create_db(files)
        index.conf['db_default_file'] = None
        p = projects.Projects(db_path=db)
        issues = p.validate()
        self.assertIn('Wrong date format wrong defined in template default',
                      issues)
        self.assertEqual(len(issues), 1)

        f1 = """
        project-templates:
          default:
            uri: https://github.com/%(name)s
            gitweb: https://github.com/openstack/%(name)s/commit/%%(sha)s
        """
        files = {'f1.yaml': f1}
        db = self.create_db(files)
        index.conf['db_default_file'] = None
        p = projects.Projects(db_path=db)
        issues = p.validate()
        self.assertIn("'branches' is a required property",
                      issues)
        self.assertEqual(len(issues), 1)

        f1 = """
        projects:
          Barbican:
            openstack/barbican:
              uri: https://github.com/%(name)s
              template: default
        """
        files = {'f1.yaml': f1}
        db = self.create_db(files)
        index.conf['db_default_file'] = None
        p = projects.Projects(db_path=db)
        issues = p.validate()
        self.assertIn("Additional properties are not allowed"
                      " ('uri' was unexpected)",
                      issues)
        self.assertEqual(len(issues), 1)

    def test_get_projects(self):
        f1 = """
        project-templates:
          default:
            uri: https://bitbucket.com/%(name)s
            branches:
            - master
            - ocata
            gitweb: https://bitbucket.com/%(name)s/commit/%%(sha)s

        projects:
          Barbican:
            openstack/barbican:
              template: default
            openstack/python-barbicanclient:
              template: default
          Swift:
            openstack/swift:
              template: default
            openstack/python-swiftclient:
              template: default
              branches:
              - master
              - 1.0-dev
              - 2.0-dev
        """
        files = {'f1.yaml': f1}
        db = self.create_db(files)
        index.conf['db_default_file'] = None
        p = projects.Projects(db_path=db)
        self.assertEqual(len(p.get_projects()['Swift']), 5)
        self.assertEqual(len(p.get_projects()['Barbican']), 4)
        branches = [ref['branch'] for ref in p.get_projects()["Swift"] if
                    ref['name'] == 'openstack/python-swiftclient']
        self.assertListEqual(branches, ['master', '1.0-dev', '2.0-dev'])

    def test_get_tags(self):
        f1 = """
        project-templates:
          default:
            uri: https://bitbucket.com/%(name)s
            branches:
            - master
            - ocata
            gitweb: https://bitbucket.com/%(name)s/commit/%%(sha)s
            tags:
            - openstack
            - cloud

        projects:
          Barbican:
            openstack/barbican:
              template: default
              tags:
              - credentials
              - server
            openstack/python-barbicanclient:
              template: default
              tags:
              - credentials
              - client
          Swift:
            openstack/swift:
              template: default
              tags:
              - storage
              - server
            openstack/python-swiftclient:
              template: default
              tags:
              - storage
              - client
        """
        files = {'f1.yaml': f1}
        db = self.create_db(files)
        index.conf['db_default_file'] = None
        p = projects.Projects(db_path=db)
        tags = p.get_tags()
        self.assertEqual(len(tags['credentials']), 4)
        self.assertEqual(len(tags['storage']), 4)
        self.assertEqual(len(tags.keys()), 6)
        for tag in ('openstack', 'cloud', 'client', 'server',
                    'credentials', 'storage'):
            self.assertIn(tag, tags.keys())
