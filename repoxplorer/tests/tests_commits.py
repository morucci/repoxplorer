from unittest import TestCase

from repoxplorer import index
from repoxplorer.index.commits import Commits


class TestCommits(TestCase):

    def setUp(self):
        self.con = index.Connector()
        self.c = Commits(self.con)
        self. commits = [{
            'sha': '3597334f2cb10772950c97ddf2f6cc17b184',
            'author_date': 1410456005,
            'committer_date': 1410456005,
            'author_name': 'Nakata Daisuke',
            'committer_name': 'Nakata Daisuke',
            'author_email': 'n.suke@joker.org',
            'committer_email': 'n.suke@joker.org',
            'project_branch': 'master',
            'project_uri': 'https://github.com/nakata/monkey.git',
            'project_name': 'monkey',
            'lines_modified': 77,
            'commit_msg': 'Add init method',
        }]
        for commit in self.commits:
            self.c.add_commit(commit)

    def tearDown(self):
        self.con.ic.delete(index=self.con.index)

    def test_get_commit(self):
        ret = self.c.get_commit(
            self.c.uuid('https://github.com/nakata/monkey.git', 'master'))
        self.assertEqual(ret['commit_msg'], 'Add init method')

    def test_get_commits(self):
        ret = self.c.get_commits(author_email='n.suke@joker.org')
        self.assertEqual(ret[1], 1)
        self.assertEqual(ret[2][0]['commit_msg'], 'Add init method')
