from unittest import TestCase

from repoxplorer import index
from repoxplorer.index.commits import Commits
from repoxplorer.trends.commits import CommitsAmountTrend


class TestCommitsAmountTrend(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.con = index.Connector(index='repoxplorertest')
        cls.c = Commits(cls.con)
        cls.t = CommitsAmountTrend(cls.con)
        cls.commits = [
            {
                'sha': '3597334f2cb10772950c97ddf2f6cc17b184',
                'author_date': 1410456005,
                'committer_date': 1410456010,
                'ttl': 5,
                'author_name': 'Nakata Daisuke',
                'committer_name': 'Nakata Daisuke',
                'author_email': 'n.suke@joker.org',
                'committer_email': 'n.suke@joker.org',
                'repos': [
                    'https://github.com/nakata/monkey.git:monkey:master', ],
                'line_modifieds': 10,
                'merge_commit': False,
                'commit_msg': 'Add init method',
            },
            {
                'sha': '3597334f2cb10772950c97ddf2f6cc17b185',
                'author_date': 1410457005,
                'committer_date': 1410457005,
                'ttl': 0,
                'author_name': 'Keiko Amura',
                'committer_name': 'Keiko Amura',
                'author_email': 'keiko.a@joker.org',
                'committer_email': 'keiko.a@joker.org',
                'repos': [
                    'https://github.com/nakata/monkey.git:monkey:master', ],
                'line_modifieds': 100,
                'merge_commit': False,
                'commit_msg': 'Merge "Fix sanity unittest"',
            },
            {
                'sha': '3597334f2cb10772950c97ddf2f6cc17b186',
                'author_date': 1410458005,
                'committer_date': 1410458005,
                'ttl': 0,
                'author_name': 'Jean Bon',
                'committer_name': 'Jean Bon',
                'author_email': 'jean.bon@joker.org',
                'committer_email': 'jean.bon@joker.org',
                'repos': [
                    'https://github.com/nakata/monkey.git:monkey:master', ],
                'line_modifieds': 200,
                'merge_commit': False,
                'commit_msg': 'Add request customer feature 19',
            },
        ]
        cls.c.add_commits(cls.commits)

    @classmethod
    def tearDownClass(cls):
        cls.con.ic.delete(index=cls.con.index)

    def test_get_trend(self):
        ret = self.t.get_trend(
            repos=['https://github.com/nakata/monkey.git:monkey:master'],
            period_a=(1410457000, 1410459000),
            period_b=(1410456005, 1410456015))
        self.assertEqual(ret[0], 1)
        self.assertEqual(ret[1], 50)

        ret = self.t.get_trend(
            repos=['https://github.com/nakata/monkey.git:monkey:master'],
            period_a=(1410457000, 1410459000),
            period_b=(1410455005, 1410455015))
        self.assertEqual(ret[0], 2)
        self.assertEqual(ret[1], 100)

        ret = self.t.get_trend(
            repos=['https://github.com/nakata/monkey.git:monkey:master'],
            period_a=(1410455005, 1410455015),
            period_b=(1410457000, 1410459000))
        self.assertEqual(ret[0], -2)
        self.assertEqual(ret[1], -100)
