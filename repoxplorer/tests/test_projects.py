import os
import yaml
import shutil
import tempfile
from jsonschema import validate
from unittest import TestCase

from repoxplorer.index import projects
from repoxplorer.index import yamlbackend
from repoxplorer import index


class TestProjects(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.con = index.Connector(index='repoxplorertest')

    @classmethod
    def tearDownClass(cls):
        cls.con.ic.delete(index=cls.con.index)

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
        validate(yaml.load(projects.project_templates_example,
                           Loader=yamlbackend.NoDatesSafeLoader),
                 yaml.load(projects.project_templates_schema))

    def test_projects_schema(self):
        validate(yaml.load(projects.projects_example,
                           Loader=yamlbackend.NoDatesSafeLoader),
                 yaml.load(projects.projects_schema))

    def simple_provision(self, data=None):
        f1 = """
        project-templates:
          default:
            uri: https://bitbucket.com/%(name)s
            branches:
            - master
            gitweb: https://bitbucket.com/%(name)s/commit/%%(sha)s

        projects:
          Barbican:
            repos:
              openstack/barbican:
                template: default
        """
        files = {'f1.yaml': data or f1}
        self.db = self.create_db(files)
        index.conf['db_default_file'] = None
        projects.Projects(
            db_path=self.db, con=self.con, dump_yaml_in_index=True)

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
            repos:
              openstack/barbican:
                template: mytemplate
        """
        files = {'f1.yaml': f1, 'f2.yaml': f2}
        db = self.create_db(files)
        index.conf['db_default_file'] = None
        with self.assertRaises(RuntimeError) as exc:
            projects.Projects(
                db_path=db, con=self.con, dump_yaml_in_index=True)
            self.assertIn("Project ID 'Barbican' Repo ID 'openstack/barbican' "
                          "references an unknown template mytemplate",
                          exc)
            self.assertEqual(len(exc), 1)

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
        with self.assertRaises(RuntimeError) as exc:
            projects.Projects(
                db_path=db, con=self.con, dump_yaml_in_index=True)
            self.assertIn(
                'Wrong date format wrong defined in template default',
                exc)
            self.assertEqual(len(exc), 1)

        f1 = """
        project-templates:
          default:
            uri: https://github.com/%(name)s
            gitweb: https://github.com/openstack/%(name)s/commit/%%(sha)s
        """
        files = {'f1.yaml': f1}
        db = self.create_db(files)
        index.conf['db_default_file'] = None
        with self.assertRaises(RuntimeError) as exc:
            projects.Projects(
                db_path=db, con=self.con, dump_yaml_in_index=True)
            self.assertIn("'branches' is a required property",
                          exc)
            self.assertEqual(len(exc), 1)

        f1 = """
        projects:
          Barbican:
            repos:
              openstack/barbican:
                uri: https://github.com/%(name)s
                template: default
        """
        files = {'f1.yaml': f1}
        db = self.create_db(files)
        index.conf['db_default_file'] = None
        with self.assertRaises(RuntimeError) as exc:
            projects.Projects(
                db_path=db, con=self.con, dump_yaml_in_index=True)
            self.assertIn("Additional properties are not allowed"
                          " ('uri' was unexpected)", exc)
            self.assertEqual(len(exc), 1)

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
            logo: https://logo.png
            description: Credentials storage
            repos:
              openstack/barbican:
                template: default
              openstack/python-barbicanclient:
                template: default
          Swift:
            repos:
              openstack/swift:
                template: default
              openstack/python-swiftclient:
                template: default
                branches:
                - master
                - 1.0-dev
                - 2.0-dev
        """
        self.simple_provision(data=f1)
        p = projects.Projects(db_path=self.db, con=self.con)
        self.assertEqual(len(p.get_projects()['Swift']['refs']), 5)
        self.assertEqual(len(p.get_projects()['Barbican']['refs']), 4)
        branches = [
            ref['branch'] for ref in p.get_projects()["Swift"]['refs'] if
            ref['name'] == 'openstack/python-swiftclient']
        self.assertListEqual(branches, ['master', '1.0-dev', '2.0-dev'])

        p = projects.Projects(con=self.con)
        self.assertEqual(len(p.get_projects()['Swift']['refs']), 5)

    def test_get_by_id(self):
        self.simple_provision()
        p = projects.Projects(
            db_path=self.db, con=self.con)
        project = p.get('Barbican')
        self.assertEqual(project['name'], 'Barbican')

    def test_get_gitweb_link(self):
        self.simple_provision()
        p = projects.Projects(
            db_path=self.db, con=self.con)
        link = p.get_gitweb_link(
            ('https://bitbucket.com/openstack/barbican:'
             'openstack/barbican:master'))
        self.assertEqual(
            link, 'https://bitbucket.com/openstack/barbican/commit/%(sha)s')
        link = p.get_gitweb_link('notexists')
        self.assertEqual(link, '')

    def test_get_projects_from_references(self):
        f1 = """
        project-templates:
          default:
            uri: https://bitbucket.com/%(name)s
            branches:
            - master
            gitweb: https://bitbucket.com/%(name)s/commit/%%(sha)s

        projects:
          Barbican:
            repos:
              openstack/barbican:
                template: default
          Swift:
            repos:
              openstack/barbican:
                template: default
          Nova:
            repos:
              openstack/nova:
                template: default
        """
        self.simple_provision(data=f1)
        p = projects.Projects(
            db_path=self.db, con=self.con)
        refs = [('https://bitbucket.com/openstack/barbican:'
                 'openstack/barbican:master'),
                ('https://bitbucket.com/openstack/swift:'
                 'openstack/swift:master')]
        ret = p.get_projects_from_references(refs)
        self.assertListEqual(['Swift', 'Barbican'], ret)

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
            repos:
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
            repos:
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
        self.simple_provision(data=f1)
        p = projects.Projects(db_path=self.db, con=self.con)
        tags = p.get_tags()
        self.assertEqual(len(tags['credentials']['refs']), 4)
        self.assertEqual(len(tags['storage']['refs']), 4)
        self.assertEqual(len(tags.keys()), 6)
        for tag in ('openstack', 'cloud', 'client', 'server',
                    'credentials', 'storage'):
            self.assertIn(tag, tags.keys())
