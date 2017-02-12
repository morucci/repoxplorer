from repoxplorer import index
from repoxplorer.tests import FunctionalTest
from repoxplorer.index.commits import Commits
from repoxplorer.index.tags import Tags

from repoxplorer.controllers import root

from mock import patch


class TestRootController(FunctionalTest):

    @classmethod
    def setUpClass(cls):
        cls.con = index.Connector(index='repoxplorertest')
        cls.c = Commits(cls.con)
        cls.t = Tags(cls.con)
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
                'repos': [
                    'https://github.com/nakata/monkey.git:monkey:master', ],
                'line_modifieds': 10,
                'merge_commit': False,
                'commit_msg': 'Add init method',
                'implement': ['feature 35', ],
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
                'repos': [
                    'https://github.com/nakata/monkey.git:monkey:master', ],
                'line_modifieds': 10,
                'merge_commit': False,
                'commit_msg': 'Add feature 36',
                'implement': ['feature 36', ],
                'close-bug': ['18', ],
            },
            {
                'sha': '3597334f2cb10772950c97ddf2f6cc17b1846',
                'author_date': 1410456005,
                'committer_date': 1410456005,
                'ttl': 0,
                'author_name': 'Jean Marc',
                'committer_name': 'Jean Marc',
                'author_email': 'j.marc@joker2.org',
                'committer_email': 'j.marc@joker2.org',
                'repos': [
                    'https://github.com/nakata/monkey.git:monkey:master', ],
                'line_modifieds': 0,
                'merge_commit': True,
                'commit_msg': 'Merge: something',
            }]
        cls.c.add_commits(cls.commits)
        cls.projects = {'test': [
            {'uri': 'https://github.com/nakata/monkey.git',
             'name': 'monkey',
             'branch': 'master'}]}
        cls.tags = [
            {
                'sha': '3597334f2cb10772950c97ddf2f6cc17b184',
                'date': 1410456005,
                'repo':
                    'https://github.com/nakata/monkey.git:monkey',
                'name': 'tag1',
            },
            {
                'sha': '3597334f2cb10772950c97ddf2f6cc17b1845',
                'date': 1410456005,
                'repo':
                    'https://github.com/nakata/monkey.git:monkey',
                'name': 'tag2',
            }]
        cls.t.add_tags(cls.tags)

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
                '/commits.json?pid=test&metadata=implement:feature 35')
        assert response.status_int == 200
        self.assertEqual(response.json[2][0]['author_name'],
                         'Nakata Daisuke')
        with patch.object(root.Projects, 'get_projects') as m:
            root.indexname = 'repoxplorertest'
            m.return_value = self.projects
            response = self.app.get(
                '/commits.json?pid=test&metadata=implement:feature 36')
        assert response.status_int == 200
        self.assertEqual(response.json[2][0]['author_name'],
                         'Jean Paul')
        with patch.object(root.Projects, 'get_projects') as m:
            root.indexname = 'repoxplorertest'
            m.return_value = self.projects
            response = self.app.get(
                '/commits.json?pid=test&metadata='
                'implement:feature 36,close-bug:18')
        assert response.status_int == 200
        self.assertEqual(response.json[2][0]['author_name'],
                         'Jean Paul')
        with patch.object(root.Projects, 'get_projects') as m:
            root.indexname = 'repoxplorertest'
            m.return_value = self.projects
            response = self.app.get(
                '/commits.json?pid=test&metadata=implement:*')
        assert response.status_int == 200
        self.assertEqual(response.json[1], 2)
        with patch.object(root.Projects, 'get_projects') as m:
            root.indexname = 'repoxplorertest'
            m.return_value = self.projects
            response = self.app.get(
                '/commits.json?pid=test&inc_merge_commit=on')
        assert response.status_int == 200
        self.assertEqual(response.json[1], 3)

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

    def test_get_tags(self):
        with patch.object(root.Projects, 'get_projects') as m:
            root.indexname = 'repoxplorertest'
            m.return_value = self.projects
            response = self.app.get('/tags.json?pid=test')
            assert response.status_int == 200
            tag1 = [t for t in response.json if t['name'] == 'tag1'][0]
            tag2 = [t for t in response.json if t['name'] == 'tag2'][0]
            self.assertDictEqual(tag2, {
                u'name': u'tag2',
                u'sha': u'3597334f2cb10772950c97ddf2f6cc17b1845',
                u'date': 1410456005,
                u'repo':
                    u'https://github.com/nakata/monkey.git:monkey'})
            self.assertDictEqual(tag1, {
                u'name': u'tag1',
                u'sha': u'3597334f2cb10772950c97ddf2f6cc17b184',
                u'date': 1410456005,
                u'repo':
                    u'https://github.com/nakata/monkey.git:monkey'})

    def test_get_projects(self):
        with patch.object(root.Projects, 'get_projects') as m:
            root.indexname = 'repoxplorertest'
            m.return_value = self.projects
            response = self.app.get('/projects.json?')
            assert response.status_int == 200
            self.assertIn('test', response.json['projects'])
