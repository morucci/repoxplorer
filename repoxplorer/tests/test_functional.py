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
                'implement': 'feature 35',
            },
            {
                'sha': '3597334f2cb10772950c97ddf2f6cc17b1845',
                'author_date': 1410456005,
                'committer_date': 1410456005,
                'ttl': 0,
                'author_name': 'Jean Paul',
                'committer_name': 'Jean Paul',
                'author_email': 'j.paul@joker.org',
                'committer_email': 'j.paul@joker.org',
                'projects': [
                    'https://github.com/nakata/monkey.git:monkey:master', ],
                'line_modifieds': 10,
                'merge_commit': False,
                'commit_msg': 'Add feature 36',
                'implement': 'feature 36',
                'close-bug': '18',
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
        with patch.object(root.Projects, 'get_projects') as m:
            root.indexname = 'repoxplorertest'
            m.return_value = self.projects
            response = self.app.get(
                '/commits.json?pid=test&metadata=implement=feature 35')
        assert response.status_int == 200
        self.assertEqual(response.json[2][0]['author_name'],
                         'Nakata Daisuke')
        with patch.object(root.Projects, 'get_projects') as m:
            root.indexname = 'repoxplorertest'
            m.return_value = self.projects
            response = self.app.get(
                '/commits.json?pid=test&metadata=implement=feature 36')
        assert response.status_int == 200
        self.assertEqual(response.json[2][0]['author_name'],
                         'Jean Paul')
        with patch.object(root.Projects, 'get_projects') as m:
            root.indexname = 'repoxplorertest'
            m.return_value = self.projects
            response = self.app.get(
                '/commits.json?pid=test&metadata='
                'implement=feature 36,close-bug=18')
        assert response.status_int == 200
        self.assertEqual(response.json[2][0]['author_name'],
                         'Jean Paul')
        with patch.object(root.Projects, 'get_projects') as m:
            root.indexname = 'repoxplorertest'
            m.return_value = self.projects
            response = self.app.get(
                '/commits.json?pid=test&metadata=implement=*')
        assert response.status_int == 200
        self.assertEqual(response.json[1], 2)

    def test_get_metadata(self):
        with patch.object(root.Projects, 'get_projects') as m:
            root.indexname = 'repoxplorertest'
            m.return_value = self.projects
            response = self.app.get('/metadata.json?pid=test')
            assert response.status_int == 200
            self.assertDictEqual(
                response.json,
                {u'implement': 2, u'close-bug': 1})
            response = self.app.get('/metadata.json?key=implement&pid=test')
            assert response.status_int == 200
            self.assertIn('feature 35', response.json)
            self.assertIn('feature 36', response.json)
            self.assertEqual(len(response.json), 2)
