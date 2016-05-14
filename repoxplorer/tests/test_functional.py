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
                'author_name': 'Nakata Daisuke',
                'committer_name': 'Nakata Daisuke',
                'author_email': 'n.suke@joker.org',
                'committer_email': 'n.suke@joker.org',
                'project':
                    'https://github.com/nakata/monkey.git:monkey:master',
                'line_modifieds': 10,
                'commit_msg': 'Add init method',
            }]
        for commit in cls.commits:
            cls.c.add_commit(commit)
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
        root.indexname = 'repoxplorertest'
        req = {'mails': [],
               'projects': [
                   'https://github.com/nakata/monkey.git:monkey:master'],
               'fromdate': None,
               'todate': None,
               'start': 0,
               'limit': 15}
        response = self.app.post_json('/commits.json', req)
        assert response.status_int == 200
        self.assertEqual(response.json[2][0]['author_email'],
                         'n.suke@joker.org')
