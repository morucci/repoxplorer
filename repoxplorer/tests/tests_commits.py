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
                'project':
                    'https://github.com/nakata/monkey.git:monkey:master',
                'lines_modified': 10,
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
                'project':
                    'https://github.com/amura/kotatsu.git:kotatsu:master',
                'lines_modified': 100,
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
                'project':
                    'https://github.com/nakata/monkey.git:monkey:master',
                'lines_modified': 200,
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
                'project':
                    'https://github.com/nakata/monkey.git:monkey:master',
                'lines_modified': 300,
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
                'project':
                    'https://github.com/amura/kotatsu.git:kotatsu:master',
                'lines_modified': 400,
                'commit_msg': 'Add request customer feature 21',
            },
            {
                'sha': '3597334f2cb10772950c97ddf2f6cc17b188',
                'author_date': 1410460005,
                'committer_date': 1410460005,
                'author_name': 'Jean Bon',
                'committer_name': 'Jean Bon',
                'author_email': 'jean.bon@joker.org',
                'committer_email': 'jean.bon@joker.org',
                'project':
                    'https://github.com/amura/kotatsu.git:kotatsu:devel',
                'lines_modified': 400,
                'commit_msg': 'Add request customer feature 21',
            },
            {
                'sha': '3597334f2cb10772950c97ddf2f6cc17b189',
                'author_date': 1410461005,
                'committer_date': 1410461005,
                'author_name': 'Jean Bon',
                'committer_name': 'Jean Bon',
                'author_email': 'jean.bon@joker.org',
                'committer_email': 'jean.bon@joker.org',
                'project':
                    'https://github.com/amura/kotatsu.git:kotatsu:devel',
                'lines_modified': 400,
                'commit_msg': 'Add request customer feature 22',
            },
            {
                'sha': '3597334f2cb10772950c97ddf2f6cc17b190',
                'author_date': 1410491005,
                'committer_date': 1410491005,
                'author_name': 'Jean Bon',
                'committer_name': 'Jean Bon',
                'author_email': 'jean.bon@joker.org',
                'committer_email': 'jean.bon@joker.org',
                'project':
                    'https://github.com/amura/kotatsu.git:kotatsu:devel',
                'lines_modified': 400,
                'commit_msg': 'Add request customer feature 23',
            }
        ]
        for commit in self.commits:
            self.c.add_commit(commit)

    def tearDown(self):
        self.con.ic.delete(index=self.con.index)

    def test_get_commit(self):
        ret = self.c.get_commit('3597334f2cb10772950c97ddf2f6cc17b188')
        print ret
        self.assertEqual(ret['commit_msg'], 'Add request customer feature 21')

    def test_get_commits(self):
        ret = self.c.get_commits(mails=['n.suke@joker.org'])
        self.assertEqual(ret[1], 1)
        self.assertEqual(ret[2][0]['commit_msg'], 'Add init method')

        ret = self.c.get_commits(mails=['jean.bon@joker.org'])
        self.assertEqual(ret[1], 5)
        self.assertEqual(ret[2][0]['commit_msg'],
                         'Add request customer feature 23')

        ret = self.c.get_commits(
            projects=['https://github.com/amura/kotatsu.git:kotatsu:master'])
        self.assertEqual(ret[1], 2)
        self.assertEqual(ret[2][0]['commit_msg'],
                         'Add request customer feature 21')

        ret = self.c.get_commits(
            projects=['https://github.com/nakata/monkey.git:monkey:master'],
            mails=['jean.bon@joker.org'])
        self.assertEqual(ret[1], 2)
        self.assertEqual(ret[2][0]['commit_msg'],
                         'Add request customer feature 20')

        ret = self.c.get_commits(
            projects=['https://github.com/nakata/monkey.git:monkey:master'])
        self.assertEqual(ret[1], 3)

        ret = self.c.get_commits(
            projects=['https://github.com/nakata/monkey.git:monkey:master'],
            fromdate=1410456000,
            todate=1410458010,)
        self.assertEqual(ret[1], 2)
        self.assertEqual(ret[2][0]['commit_msg'],
                         'Add request customer feature 19')

        ret = self.c.get_commits(
            projects=['https://github.com/amura/kotatsu.git:kotatsu:devel',
                      'https://github.com/amura/kotatsu.git:kotatsu:master'])
        self.assertEqual(ret[1], 4)

    def test_get_commits_amount(self):
        ret = self.c.get_commits_amount(
            ['n.suke@joker.org'])
        self.assertEqual(ret, 1)

        ret = self.c.get_commits_amount(
            ['n.suke@joker.org',
             'jean.bon@joker.org'])
        self.assertEqual(ret, 6)

        ret = self.c.get_commits_amount(
            ['n.suke@joker.org',
             'jean.bon@joker.org'],
            fromdate=1410456000,
            todate=1410456010)
        self.assertEqual(ret, 1)

        ret = self.c.get_commits_amount(
            projects=['https://github.com/nakata/monkey.git:monkey:master'])
        self.assertEqual(ret, 3)

        ret = self.c.get_commits_amount(
            ['n.suke@joker.org'],
            projects=['https://github.com/nakata/monkey.git:monkey:master'])
        self.assertEqual(ret, 1)

        ret = self.c.get_commits_amount(
            ['jean.bon@joker.org'],
            projects=['https://github.com/nakata/monkey.git:monkey:master'])
        self.assertEqual(ret, 2)

        ret = self.c.get_commits_amount(
            ['jean.bon@joker.org'],
            projects=['https://github.com/nakata/monkey.git:monkey:master',
                      'https://github.com/amura/kotatsu.git:kotatsu:master'])
        self.assertEqual(ret, 3)

        ret = self.c.get_commits_amount(
            ['jean.bon@joker.org', 'keiko.a@joker.org'],
            projects=['https://github.com/nakata/monkey.git:monkey:master',
                      'https://github.com/amura/kotatsu.git:kotatsu:master'])
        self.assertEqual(ret, 4)

    def test_get_lines_modified_amount(self):
        ret = self.c.get_lines_modified_stats(
            ['n.suke@joker.org'])
        self.assertDictEqual(ret[1], {u'avg': 10.0, u'min': 10.0,
                                      u'count': 1, u'max': 10.0,
                                      u'sum': 10.0})

        ret = self.c.get_lines_modified_stats(
            ['jean.bon@joker.org'],
            projects=['https://github.com/nakata/monkey.git:monkey:master',
                      'https://github.com/amura/kotatsu.git:kotatsu:master'])
        self.assertDictEqual(ret[1], {u'avg': 300.0, u'min': 200.0,
                                      u'max': 400.0, u'count': 3,
                                      u'sum': 900.0})

    def test_get_top_authors(self):
        ret = self.c.get_top_authors(
            projects=['https://github.com/nakata/monkey.git:monkey:master'])
        self.assertDictEqual(ret[1], {u'jean.bon@joker.org': 2,
                                      u'n.suke@joker.org': 1})

        ret = self.c.get_top_authors(
            projects=['https://github.com/nakata/monkey.git:monkey:master',
                      'https://github.com/amura/kotatsu.git:kotatsu:master'])
        self.assertDictEqual(ret[1], {u'jean.bon@joker.org': 3,
                                      u'keiko.a@joker.org': 1,
                                      u'n.suke@joker.org': 1})

    def test_get_top_projects(self):
        ret = self.c.get_top_projects(
            ['jean.bon@joker.org'])
        self.assertDictEqual(ret[1], {
            u'https://github.com/amura/kotatsu.git:kotatsu:devel': 3,
            u'https://github.com/amura/kotatsu.git:kotatsu:master': 1,
            u'https://github.com/nakata/monkey.git:monkey:master': 2})

    def test_get_commits_histo(self):
        ret = self.c.get_commits_histo(
            ['jean.bon@joker.org'])
        self.assertDictEqual(ret[1][0], {u'key': 1410393600000,
                                         u'doc_count': 4,
                                         u'key_as_string': u'2014-09-11'})
        self.assertDictEqual(ret[1][1], {u'key': 1410480000000,
                                         u'doc_count': 1,
                                         u'key_as_string': u'2014-09-12'})
        ret = self.c.get_commits_histo(
            ['jean.bon@joker.org'],
            projects=['https://github.com/amura/kotatsu.git:kotatsu:devel'])
        self.assertDictEqual(ret[1][0], {u'key': 1410393600000,
                                         u'doc_count': 2,
                                         u'key_as_string': u'2014-09-11'})
        self.assertDictEqual(ret[1][1], {u'key': 1410480000000,
                                         u'doc_count': 1,
                                         u'key_as_string': u'2014-09-12'})
