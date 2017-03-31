import os
import yaml
import shutil
import tempfile
from jsonschema import validate
from unittest import TestCase

from repoxplorer.index import projects


class TestProjects(TestCase):

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

    def test_project_templates_schema(self):
        validate(yaml.load(projects.project_templates_example),
                 yaml.load(projects.project_templates_schema))

    def test_projects_schema(self):
        validate(yaml.load(projects.projects_example),
                 yaml.load(projects.projects_schema))

    def test_projects_get(self):
        f1 = """
        project-templates:
          mytemplate:
            uri: https://bitbucket.com/%(name)s
            branches:
            - master
            gitweb: https://bitbucket.com/%(name)s/commit/%%(sha)s

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

        projects:
          Barbican:
            openstack/barbican:
              template: default
            openstack/python-barbicanclient:
              template: default
          Nova:
            openstack/nova:
              template: default
            openstack/python-novaclient:
              template: default
        """
        files = {'f1.yaml': f1, 'default.yaml': default}
        db = self.create_db(files)
        projects.conf['db_default_file'] = os.path.join(db,
                                                        'default.yaml')
        p = projects.Projects(db_path=db)
        ret = p.get_projects()
        print ret
