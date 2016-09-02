from repoxplorer import index
from repoxplorer.tests import FunctionalTest
from repoxplorer.index.commits import Commits

from repoxplorer.controllers import root

from mock import patch


class TestRootController(FunctionalTest):

    @classmethod
    def setUpClass(cls):
        cls.con = index.Connector(index='repoxplorertest')
        cls.c = Commits(cls.con)
        cls.commits = [
            {
                'sha': '3597334f2cb10772950c97ddf2f6cc17b184',
                'author_date': 1410456005,
                'committer_date': 1410456005,
                'ttl': 0,
                'author_name': 'Nakata Daisuke',
                'committer_name': 'Nakata Daisuke',
                'author_email': 'n.suke@joker.org',
                'committer_email': 'n.suke@joker.org',
                'projects': [
                    'https://github.com/nakata/monkey.git:monkey:master', ],
                'line_modifieds': 10,
                'merge_commit': False,
                'commit_msg': 'Add init method',
            }]
        cls.c.add_commits(cls.commits)
        cls.projects = {'test': [
            {'uri': 'https://github.com/nakata/monkey.git',
             'name': 'monkey',
             'branch': 'master'}]}

    @classmethod
    def tearDownClass(cls):
        cls.con.ic.delete(index=cls.con.index)

    def test_get_index(self):
        response = self.app.get('/')
        assert response.status_int == 200

    def test_get_project_page(self):
        with patch.object(root.Projects, 'get_projects') as m:
            root.indexname = 'repoxplorertest'
            m.return_value = self.projects
            response = self.app.get('/project.html?pid=test')
        assert response.status_int == 200

    def test_get_commits(self):
        with patch.object(root.Projects, 'get_projects') as m:
            root.indexname = 'repoxplorertest'
            m.return_value = self.projects
            response = self.app.get('/commits.json?pid=test')
        assert response.status_int == 200
        self.assertEqual(response.json[2][0]['author_name'],
                         'Nakata Daisuke')
