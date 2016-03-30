from unittest import TestCase

from repoxplorer import index
from repoxplorer.index.commits import Commits


class TestCommits(TestCase):

    def setUp(self):
        self.con = index.Connector()
        self.c = Commits(self.con)
        self. commits = [
            {
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
            },
            {
                'sha': '3597334f2cb10772950c97ddf2f6cc17b185',
                'author_date': 1410457005,
                'committer_date': 1410457005,
                'author_name': 'Keiko Amura',
                'committer_name': 'Keiko Amura',
                'author_email': 'keiko.a@joker.org',
                'committer_email': 'keiko.a@joker.org',
                'project_branch': 'master',
                'project_uri': 'https://github.com/amura/kotatsu.git',
                'project_name': 'kotatsu',
                'lines_modified': 177,
                'commit_msg': 'Fix sanity unittest',
            },
            {
                'sha': '3597334f2cb10772950c97ddf2f6cc17b186',
                'author_date': 1410458005,
                'committer_date': 1410458005,
                'author_name': 'Jean Bon',
                'committer_name': 'Jean Bon',
                'author_email': 'jean.bon@joker.org',
                'committer_email': 'jean.bon@joker.org',
                'project_branch': 'master',
                'project_uri': 'https://github.com/nakata/monkey.git',
                'project_name': 'monkey',
                'lines_modified': 277,
                'commit_msg': 'Add request customer feature 19',
            },
            {
                'sha': '3597334f2cb10772950c97ddf2f6cc17b187',
                'author_date': 1410459005,
                'committer_date': 1410459005,
                'author_name': 'Jean Bon',
                'committer_name': 'Jean Bon',
                'author_email': 'jean.bon@joker.org',
                'committer_email': 'jean.bon@joker.org',
                'project_branch': 'master',
                'project_uri': 'https://github.com/nakata/monkey.git',
                'project_name': 'monkey',
                'lines_modified': 377,
                'commit_msg': 'Add request customer feature 20',
            },
            {
                'sha': '3597334f2cb10772950c97ddf2f6cc17b188',
                'author_date': 1410460005,
                'committer_date': 1410460005,
                'author_name': 'Jean Bon',
                'committer_name': 'Jean Bon',
                'author_email': 'jean.bon@joker.org',
                'committer_email': 'jean.bon@joker.org',
                'project_branch': 'master',
                'project_uri': 'https://github.com/amura/kotatsu.git',
                'project_name': 'kotatsu',
                'lines_modified': 377,
                'commit_msg': 'Add request customer feature 21',
            }
        ]
        for commit in self.commits:
            self.c.add_commit(commit)

    def tearDown(self):
        self.con.ic.delete(index=self.con.index)

    def test_get_commit(self):
        ret = self.c.get_commit(
            self.c.uuid('https://github.com/nakata/monkey.git',
                        'master',
                        '3597334f2cb10772950c97ddf2f6cc17b184'))
        self.assertEqual(ret['commit_msg'], 'Add init method')

    def test_get_commits(self):
        ret = self.c.get_commits(mails=['n.suke@joker.org'])
        self.assertEqual(ret[1], 1)
        self.assertEqual(ret[2][0]['commit_msg'], 'Add init method')

        ret = self.c.get_commits(mails=['jean.bon@joker.org'])
        self.assertEqual(ret[1], 3)
        self.assertEqual(ret[2][0]['commit_msg'],
                         'Add request customer feature 21')

        ret = self.c.get_commits(
            projects=[{'project_uri': 'https://github.com/amura/kotatsu.git',
                       'project_name': 'kotatsu',
                       'project_branch': 'master'}])
        self.assertEqual(ret[1], 2)
        self.assertEqual(ret[2][0]['commit_msg'],
                         'Add request customer feature 21')

        ret = self.c.get_commits(
            projects=[{'project_uri': 'https://github.com/nakata/monkey.git',
                       'project_name': 'monkey',
                       'project_branch': 'master'}],
            mails=['jean.bon@joker.org'])
        self.assertEqual(ret[1], 2)
        self.assertEqual(ret[2][0]['commit_msg'],
                         'Add request customer feature 20')

        ret = self.c.get_commits(
            projects=[{'project_uri': 'https://github.com/nakata/monkey.git',
                       'project_name': 'monkey',
                       'project_branch': 'master'}])
        self.assertEqual(ret[1], 3)

        ret = self.c.get_commits(
            projects=[{'project_uri': 'https://github.com/nakata/monkey.git',
                       'project_name': 'monkey',
                       'project_branch': 'master'}],
            fromdate=1410456000,
            todate=1410458010,)
        self.assertEqual(ret[1], 2)
        self.assertEqual(ret[2][0]['commit_msg'],
                         'Add request customer feature 19')

    def test_get_commits_amount_by_author(self):
        ret = self.c.get_commits_amount(
            ['n.suke@joker.org'])
        self.assertEqual(ret[1], 1)

        ret = self.c.get_commits_amount(
            ['n.suke@joker.org',
             'jean.bon@joker.org'])
        self.assertEqual(ret[1], 4)

        ret = self.c.get_commits_amount(
            ['n.suke@joker.org',
             'jean.bon@joker.org'],
            fromdate=1410456000,
            todate=1410456010)
        self.assertEqual(ret[1], 1)

        ret = self.c.get_commits_amount(
            projects=[{'project_uri': 'https://github.com/nakata/monkey.git',
                       'project_name': 'monkey',
                       'project_branch': 'master'}])
        self.assertEqual(ret[1], 3)

        ret = self.c.get_commits_amount(
            ['n.suke@joker.org'],
            [{'project_uri': 'https://github.com/nakata/monkey.git',
              'project_name': 'monkey',
              'project_branch': 'master'}])
        self.assertEqual(ret[1], 1)

        ret = self.c.get_commits_amount(
            ['jean.bon@joker.org'],
            [{'project_uri': 'https://github.com/nakata/monkey.git',
              'project_name': 'monkey',
              'project_branch': 'master'}])
        self.assertEqual(ret[1], 2)

        ret = self.c.get_commits_amount(
            ['jean.bon@joker.org'],
            [{'project_uri': 'https://github.com/nakata/monkey.git',
              'project_name': 'monkey',
              'project_branch': 'master'},
             {'project_uri': 'https://github.com/amura/kotatsu.git',
              'project_name': 'kotatsu',
              'project_branch': 'master'}])
        self.assertEqual(ret[1], 3)

        ret = self.c.get_commits_amount(
            ['jean.bon@joker.org', 'keiko.a@joker.org'],
            [{'project_uri': 'https://github.com/nakata/monkey.git',
              'project_name': 'monkey',
              'project_branch': 'master'},
             {'project_uri': 'https://github.com/amura/kotatsu.git',
              'project_name': 'kotatsu',
              'project_branch': 'master'}])
        self.assertEqual(ret[1], 4)
