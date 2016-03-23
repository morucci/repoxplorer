from unittest import TestCase

from repoxplorer import index
from repoxplorer.index.commits import Commits


class TestCommits(TestCase):

    def setUp(self):
        self.con = index.Connector()

    def tearDown(self):
        pass

    def test_commit(self):
        c = Commits(self.con)
        commit = {
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
        }
        c.add_commit(commit)
        ret = c.get_commit(c.uuid('https://github.com/nakata/monkey.git',
                                  'master'))
        self.assertEqual(ret['_source']['commit_msg'], 'Add init method')
