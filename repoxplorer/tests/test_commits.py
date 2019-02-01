from unittest import TestCase

from repoxplorer import index
from repoxplorer.index.commits import Commits


class TestCommits(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.con = index.Connector(index='repoxplorertest')
        cls.c = Commits(cls.con)
        cls.commits = [
            {
                'sha': '3597334f2cb10772950c97ddf2f6cc17b184',
                'author_date': 1410456005,
                'committer_date': 1410456010,
                'ttl': 5,
                'author_name': 'Nakata Daisuke',
                'committer_name': 'Nakata Daisuke',
                'author_email': 'n.suke@joker.org',
                'author_email_domain': 'joker.org',
                'committer_email': 'n.suke@joker.org',
                'repos': [
                    'https://github.com/nakata/monkey.git:monkey:master', ],
                'line_modifieds': 10,
                'merge_commit': False,
                'commit_msg': 'Add init method',
                'implement-partial-epic': ['Great Feature', ],
                'files_list': [
                    'ichi/',
                    'ichi/ni/kuruma.sh',
                    'ichi/ni/san/',
                    'ichi/ni/san/tamago.txt'],
            },
            {
                'sha': '3597334f2cb10772950c97ddf2f6cc17b185',
                'author_date': 1410457005,
                'committer_date': 1410457005,
                'ttl': 0,
                'author_name': 'Keiko Amura',
                'committer_name': 'Keiko Amura',
                'author_email': 'keiko.a@hanabi.org',
                'author_email_domain': 'hanabi.org',
                'committer_email': 'keiko.a@hanabi.org',
                'repos': [
                    'https://github.com/amura/kotatsu.git:kotatsu:master', ],
                'line_modifieds': 100,
                'merge_commit': True,
                'commit_msg': 'Merge "Fix sanity unittest"',
                'files_list': [],
            },
            {
                'sha': '3597334f2cb10772950c97ddf2f6cc17b186',
                'author_date': 1410458005,
                'committer_date': 1410458005,
                'ttl': 0,
                'author_name': 'Jean Bon',
                'committer_name': 'Jean Bon',
                'author_email': 'jean.bon@joker.org',
                'author_email_domain': 'joker.org',
                'committer_email': 'jean.bon@joker.org',
                'repos': [
                    'https://github.com/nakata/monkey.git:monkey:master', ],
                'line_modifieds': 200,
                'merge_commit': False,
                'commit_msg': 'Add request customer feature 19',
                'implement-feature': ['19', ],
                'files_list': [
                    'monkey/',
                    'monkey/__init__.py',
                    'ichi/',
                    'ichi/ni/hikoki.asm'],
            },
            {
                'sha': '3597334f2cb10772950c97ddf2f6cc17b187',
                'author_date': 1410459005,
                'committer_date': 1410459005,
                'ttl': 0,
                'author_name': 'Jean Bon',
                'committer_name': 'Jean Bon',
                'author_email': 'jean.bon@joker.org',
                'author_email_domain': 'joker.org',
                'committer_email': 'jean.bon@joker.org',
                'repos': [
                    'https://github.com/nakata/monkey.git:monkey:master', ],
                'line_modifieds': 300,
                'merge_commit': False,
                'commit_msg': 'Add request customer feature 20',
                'implement-feature': ['20', ],
                'implement-partial-epic': ['Great Feature', ],
                'files_list': [],
            },
            {
                'sha': '3597334f2cb10772950c97ddf2f6cc17b188',
                'author_date': 1410460005,
                'committer_date': 1410460005,
                'ttl': 0,
                'author_name': 'Jean Bon',
                'committer_name': 'Jean Bon',
                'author_email': 'jean.bon@joker.org',
                'author_email_domain': 'joker.org',
                'committer_email': 'jean.bon@joker.org',
                'repos': [
                    'https://github.com/amura/kotatsu.git:kotatsu:master',
                    'https://github.com/amura/kotatsu.git:kotatsu:devel'],
                'line_modifieds': 400,
                'merge_commit': False,
                'commit_msg': 'Add request customer feature 21',
                'files_list': [],
            },
            {
                'sha': '3597334f2cb10772950c97ddf2f6cc17b189',
                'author_date': 1410461005,
                'committer_date': 1410461005,
                'ttl': 0,
                'author_name': 'Jean Bon',
                'committer_name': 'Jean Bon',
                'author_email': 'jean.bon@joker.org',
                'author_email_domain': 'joker.org',
                'committer_email': 'jean.bon@joker.org',
                'repos': [
                    'https://github.com/amura/kotatsu.git:kotatsu:devel', ],
                'line_modifieds': 400,
                'merge_commit': False,
                'commit_msg': 'Add request customer feature 22',
                'files_list': [],
            },
            {
                'sha': '3597334f2cb10772950c97ddf2f6cc17b190',
                'author_date': 1410491005,
                'committer_date': 1410491005,
                'ttl': 0,
                'author_name': 'Jean Bon',
                'committer_name': 'Jean Bon',
                'author_email': 'jean.bon@joker.org',
                'author_email_domain': 'joker.org',
                'committer_email': 'jean.bon@joker.org',
                'repos': [
                    'https://github.com/amura/kotatsu.git:kotatsu:devel', ],
                'line_modifieds': 400,
                'merge_commit': False,
                'commit_msg': 'Add request customer feature 23',
                'files_list': [],
            },
            {
                'sha': '3597334f2cb10772950c97ddf2f6cc17b191',
                'author_date': 46400,
                'committer_date': 46400,
                'ttl': 0,
                'author_name': 'Marty Junior',
                'committer_name': 'Marty Junior',
                'author_email': 'mcfly@joker.org',
                'author_email_domain': 'joker.org',
                'committer_email': 'mcfly@joker.org',
                'repos': [
                    'https://github.com/amura/kotatsu.git:kotatsu:devel', ],
                'line_modifieds': 400,
                'merge_commit': False,
                'commit_msg': 'Add request customer feature 23',
                'files_list': [],
            }
        ]
        cls.c.add_commits(cls.commits)

    @classmethod
    def tearDownClass(cls):
        cls.con.ic.delete(index=cls.con.index)

    def test_get_commit(self):
        ret = self.c.get_commit('3597334f2cb10772950c97ddf2f6cc17b188')
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
            repos=['https://github.com/amura/kotatsu.git:kotatsu:master'])
        self.assertEqual(ret[1], 2)
        self.assertEqual(ret[2][0]['commit_msg'],
                         'Add request customer feature 21')

        ret = self.c.get_commits(
            repos=['https://github.com/nakata/monkey.git:monkey:master'],
            mails=['jean.bon@joker.org'])
        self.assertEqual(ret[1], 2)
        self.assertEqual(ret[2][0]['commit_msg'],
                         'Add request customer feature 20')

        ret = self.c.get_commits(
            repos=['https://github.com/nakata/monkey.git:monkey:master'])
        self.assertEqual(ret[1], 3)

        ret = self.c.get_commits(
            repos=['https://github.com/nakata/monkey.git:monkey:master'],
            fromdate=1410456000,
            todate=1410458010,)
        self.assertEqual(ret[1], 2)
        self.assertEqual(ret[2][0]['commit_msg'],
                         'Add request customer feature 19')

        ret = self.c.get_commits(
            repos=['https://github.com/amura/kotatsu.git:kotatsu:devel',
                   'https://github.com/amura/kotatsu.git:kotatsu:master'])
        self.assertEqual(ret[1], 4)

        ret = self.c.get_commits(
            mails={'jean.bon@joker.org': {'begin-date': 1410461004,
                                          'end-date': 1410491006},
                   'n.suke@joker.org': {'begin-date': 1410456011}})
        self.assertEqual(ret[1], 2)

        ret = self.c.get_commits(
            mails={'jean.bon@joker.org': {'begin-date': 1410461004,
                                          'end-date': 1410491006},
                   'n.suke@joker.org': {'begin-date': 1410456011}},
            fromdate=1410461004,
            todate=1410461006,)
        self.assertEqual(ret[1], 1)

        ret = self.c.get_commits(
            mails={'jean.bon@joker.org': {'begin-date': 1410461004,
                                          'end-date': 1410491006},
                   'n.suke@joker.org': {'begin-date': 1410456009}})
        self.assertEqual(ret[1], 3)

        ret = self.c.get_commits(
            repos=['https://github.com/nakata/monkey.git:monkey:master'],
            mails={'jean.bon@joker.org': {'begin-date': 1410461004,
                                          'end-date': 1410491006},
                   'n.suke@joker.org': {'begin-date': 1410456009}})
        self.assertEqual(ret[1], 1)

        ret = self.c.get_commits(
            mails={'jean.bon@joker.org': {'begin-date': 1410461004,
                                          'end-date': 1410491006}},
            mails_neg=True)
        self.assertEqual(ret[1], 5)

        ret = self.c.get_commits(
            repos=['https://github.com/amura/kotatsu.git:kotatsu:devel'],
            mails={'jean.bon@joker.org': {'begin-date': 1410461004,
                                          'end-date': 1410491006}},
            mails_neg=True)
        self.assertEqual(ret[1], 1)
        self.assertEqual(ret[2][0]['sha'],
                         '3597334f2cb10772950c97ddf2f6cc17b188')

        ret = self.c.get_commits(
            repos={
                'https://github.com/nakata/monkey.git:monkey:master': [
                    'ichi/ni/san/']})
        self.assertEqual(ret[1], 1)

        ret = self.c.get_commits(
            repos={
                'https://github.com/nakata/monkey.git:monkey:master': [
                    'ichi/ni/san/',
                    'monkey/']})
        self.assertEqual(ret[1], 2)

        ret = self.c.get_commits(
            repos={
                'https://github.com/nakata/monkey.git:monkey:master': [
                    'ichi/ni/san/',
                    'monkey/',
                    'dame/']})
        self.assertEqual(ret[1], 2)

        ret = self.c.get_commits(
            repos={
                'https://github.com/nakata/monkey.git:monkey:master': [
                    'dame/']})
        self.assertEqual(ret[1], 0)

        ret = self.c.get_commits(
            repos={
                'https://github.com/nakata/monkey.git:monkey:master': []})
        self.assertEqual(ret[1], 3)

        ret = self.c.get_commits(
            domains=['joker.org'])
        self.assertEqual(ret[1], 6)

        ret = self.c.get_commits(
            domains=['hanabi.org'])
        self.assertEqual(ret[1], 1)

        ret = self.c.get_commits(
            domains=['hanabi.org', 'joker.org'])
        self.assertEqual(ret[1], 7)

        ret = self.c.get_commits(
            domains=['notexists.org', 'notfound.org'])
        self.assertEqual(ret[1], 0)

        ret = self.c.get_commits(
            mails={'jean.bon@joker.org': {}},
            domains=['hanabi.org'])
        self.assertEqual(ret[1], 6)

        ret = self.c.get_commits(
            mails={'jean.bon@joker.org': {},
                   'n.suke@joker.org': {}},
            domains=['hanabi.org'])
        self.assertEqual(ret[1], 7)

        ret = self.c.get_commits(
            mails={'jean.bon@joker.org': {}},
            domains=['hanabi.org'],
            mails_neg=True)
        self.assertEqual(ret[1], 1)
        self.assertEqual(ret[2][0]['author_email'],
                         'n.suke@joker.org')

    def test_get_commits_based_on_merge_info(self):
        ret = self.c.get_commits(mails=['keiko.a@hanabi.org'],
                                 merge_commit=False)
        self.assertEqual(ret[1], 0)
        ret = self.c.get_commits(mails=['keiko.a@hanabi.org'],
                                 merge_commit=True)
        self.assertEqual(ret[1], 1)
        # When merge_commit at None either merge commit or not
        # are returned
        ret = self.c.get_commits(mails=['keiko.a@hanabi.org'],
                                 merge_commit=None)
        self.assertEqual(ret[1], 1)

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
            todate=1410456011)
        self.assertEqual(ret, 1)

        ret = self.c.get_commits_amount(
            repos=['https://github.com/nakata/monkey.git:monkey:master'])
        self.assertEqual(ret, 3)

        ret = self.c.get_commits_amount(
            ['n.suke@joker.org'],
            repos=['https://github.com/nakata/monkey.git:monkey:master'])
        self.assertEqual(ret, 1)

        ret = self.c.get_commits_amount(
            ['jean.bon@joker.org'],
            repos=['https://github.com/nakata/monkey.git:monkey:master'])
        self.assertEqual(ret, 2)

        ret = self.c.get_commits_amount(
            ['jean.bon@joker.org'],
            repos=['https://github.com/nakata/monkey.git:monkey:master',
                   'https://github.com/amura/kotatsu.git:kotatsu:master'])
        self.assertEqual(ret, 3)

        ret = self.c.get_commits_amount(
            ['jean.bon@joker.org', 'keiko.a@hanabi.org'],
            repos=['https://github.com/nakata/monkey.git:monkey:master',
                   'https://github.com/amura/kotatsu.git:kotatsu:master'])
        self.assertEqual(ret, 4)

    def test_line_modifieds_stats(self):
        ret = self.c.get_line_modifieds_stats(
            mails=['n.suke@joker.org'])
        self.assertDictEqual(ret[1], {'avg': 10.0, 'min': 10.0,
                                      'count': 1, 'max': 10.0,
                                      'sum': 10.0})

        ret = self.c.get_line_modifieds_stats(
            mails=['jean.bon@joker.org'],
            repos=['https://github.com/nakata/monkey.git:monkey:master',
                   'https://github.com/amura/kotatsu.git:kotatsu:master'])
        self.assertDictEqual(ret[1], {'avg': 300.0, 'min': 200.0,
                                      'max': 400.0, 'count': 3,
                                      'sum': 900.0})

    def test_commit_ttl_stats(self):
        ret = self.c.get_ttl_stats(
            mails=['n.suke@joker.org'])
        self.assertDictEqual(ret[1], {'avg': 5.0, 'min': 5.0,
                                      'count': 1, 'max': 5.0,
                                      'sum': 5.0})

    def test_get_repos(self):
        ret = self.c.get_repos(
            ['jean.bon@joker.org'])
        self.assertDictEqual(ret[1], {
            'https://github.com/amura/kotatsu.git:kotatsu:devel': 3,
            'https://github.com/amura/kotatsu.git:kotatsu:master': 1,
            'https://github.com/nakata/monkey.git:monkey:master': 2})

    def test_get_commits_histo(self):
        ret = self.c.get_commits_histo(
            ['jean.bon@joker.org'])
        self.assertDictEqual(ret[1][0], {'key': 1410393600000,
                                         'doc_count': 4,
                                         'key_as_string': '2014-09-11'})
        self.assertDictEqual(ret[1][1], {'key': 1410480000000,
                                         'doc_count': 1,
                                         'key_as_string': '2014-09-12'})
        ret = self.c.get_commits_histo(
            ['jean.bon@joker.org'],
            repos=['https://github.com/amura/kotatsu.git:kotatsu:devel'])
        self.assertDictEqual(ret[1][0], {'key': 1410393600000,
                                         'doc_count': 2,
                                         'key_as_string': '2014-09-11'})
        self.assertDictEqual(ret[1][1], {'key': 1410480000000,
                                         'doc_count': 1,
                                         'key_as_string': '2014-09-12'})

    def test_get_authors_histo(self):
        ret = self.c.get_authors_histo(
            repos=['https://github.com/nakata/monkey.git:monkey:master'])
        self.assertDictEqual(ret[1][0],
                             {'authors_email': [
                                 'jean.bon@joker.org',
                                 'n.suke@joker.org'],
                              'key': 1410393600000,
                              'doc_count': 2,
                              'key_as_string': '2014-09-11'})

    def test_get_top_authors_by_lines(self):
        ret = self.c.get_top_authors_by_lines(
            repos=['https://github.com/nakata/monkey.git:monkey:master'])
        self.assertDictEqual(ret[1], {'n.suke@joker.org': 10.0,
                                      'jean.bon@joker.org': 500.0})

    def test_get_top_repos_by_lines(self):
        ret = self.c.get_top_repos_by_lines(
            mails=['jean.bon@joker.org'])
        self.assertDictEqual(ret[1], {
            'https://github.com/amura/kotatsu.git:kotatsu:master': 400.0,
            'https://github.com/amura/kotatsu.git:kotatsu:devel': 1200.0,
            'https://github.com/nakata/monkey.git:monkey:master': 500.0})

    def test_get_authors(self):
        ret = self.c.get_authors()
        self.assertDictEqual(ret[1], {'keiko.a@hanabi.org': 1,
                                      'jean.bon@joker.org': 5,
                                      'n.suke@joker.org': 1})

    def test_get_commits_author_name_by_emails(self):
        ret = self.c.get_commits_author_name_by_emails(
            ['keiko.a@hanabi.org', 'jean.bon@joker.org'])
        self.assertDictEqual(ret, {'jean.bon@joker.org': 'Jean Bon',
                                   'keiko.a@hanabi.org': 'Keiko Amura'})

    def test_get_commits_with_metadata_constraint(self):
        metadata = [('implement-feature', '19')]
        ret = self.c.get_commits(
            repos=['https://github.com/nakata/monkey.git:monkey:master'],
            metadata=metadata)
        self.assertEqual(ret[1], 1)
        self.assertEqual(ret[2][0]['sha'],
                         '3597334f2cb10772950c97ddf2f6cc17b186')
        metadata = [('implement-feature', None)]
        ret = self.c.get_commits(
            repos=['https://github.com/nakata/monkey.git:monkey:master'],
            metadata=metadata)
        self.assertEqual(ret[1], 2)
        shas = [c['sha'] for c in ret[2]]
        self.assertIn('3597334f2cb10772950c97ddf2f6cc17b186', shas)
        self.assertIn('3597334f2cb10772950c97ddf2f6cc17b187', shas)
        metadata = [('implement-feature', '20'),
                    ('implement-partial-epic', 'Great Feature')]
        ret = self.c.get_commits(
            repos=['https://github.com/nakata/monkey.git:monkey:master'],
            metadata=metadata)
        self.assertEqual(ret[1], 2)
        shas = [c['sha'] for c in ret[2]]
        self.assertIn('3597334f2cb10772950c97ddf2f6cc17b184', shas)
        self.assertIn('3597334f2cb10772950c97ddf2f6cc17b187', shas)

    def test_get_metadata_keys(self):
        ret = self.c.get_metadata_keys(
            repos=['https://github.com/nakata/monkey.git:monkey:master'])
        self.assertIn('implement-partial-epic', ret)
        self.assertIn('implement-feature', ret)
        self.assertDictEqual(
            ret,
            {'implement-feature': 2, 'implement-partial-epic': 2})

    def test_get_metadata_key_values(self):
        ret = self.c.get_metadata_key_values(
            'implement-feature',
            repos=['https://github.com/nakata/monkey.git:monkey:master'])
        self.assertIn('19', ret)
        self.assertIn('20', ret)
        self.assertTrue(len(ret), 2)
