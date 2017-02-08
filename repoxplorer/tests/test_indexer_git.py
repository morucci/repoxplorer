import os
import re
import mock
import shutil
import tempfile

from unittest import TestCase

from repoxplorer import index
from repoxplorer.index import commits
from repoxplorer.indexer.git import indexer


class TestExtractCmtFunctions(TestCase):

    def test_parse_commit_msg(self):
        msg = """cmt subject

body line 1
body line 2
metakey: metavalue
"""
        subject, metadatas = indexer.parse_commit_msg(msg)
        self.assertEqual(subject, 'cmt subject')
        self.assertIn((u'metakey', u'metavalue'), metadatas)
        self.assertTrue(len(metadatas) == 1)
        msg = """cmt subject

body line 1
body line 2
metakey: metavalue
metakey: metavalue2
"""
        subject, metadatas = indexer.parse_commit_msg(msg)
        self.assertEqual(subject, 'cmt subject')
        self.assertIn((u'metakey', u'metavalue'), metadatas)
        self.assertIn((u'metakey', u'metavalue2'), metadatas)
        self.assertTrue(len(metadatas) == 2)
        msg = """cmt subject

body line 1
body line 2
metakey: metavalue
author_date: 123
metakey2: metavalue2
"""
        subject, metadatas = indexer.parse_commit_msg(msg)
        self.assertEqual(subject, 'cmt subject')
        self.assertIn((u'metakey', u'metavalue'), metadatas)
        self.assertIn((u'metakey2', u'metavalue2'), metadatas)
        self.assertTrue(len(metadatas) == 2)
        msg = """cmt subject

body line 1. nokey: novalue
body line 2
metakey: metavalue
author_date: 123
metakey2:#metavalue2
"""
        subject, metadatas = indexer.parse_commit_msg(msg)
        self.assertEqual(subject, 'cmt subject')
        self.assertIn((u'metakey', u'metavalue'), metadatas)
        self.assertIn((u'metakey2', u'metavalue2'), metadatas)
        self.assertTrue(len(metadatas) == 2)
        msg = """cmt subject

body line 1
body line 2
http://metavalue
"""
        subject, metadatas = indexer.parse_commit_msg(msg)
        self.assertEqual(subject, 'cmt subject')
        self.assertTrue(len(metadatas) == 0)

        msg = """Implement feature bp-feature-cool

This patch implement blueprint bp-feature-cool. Also
it add the documentation of the feature. I included
the fix for the bug bz16 as it was releated.
body line 2
http://metavalue
"""
        p1 = re.compile('.*(blueprint) ([^ .]+).*')
        p2 = re.compile('.*(bug) ([^ .]+).*')
        parsers = [p1, p2]
        subject, metadatas = indexer.parse_commit_msg(
            msg, extra_parsers=parsers)
        self.assertEqual(subject, 'Implement feature bp-feature-cool')
        self.assertIn((u'blueprint', u'bp-feature-cool'), metadatas)
        self.assertIn((u'bug', u'bz16'), metadatas)
        self.assertTrue(len(metadatas) == 2)

    def test_get_diff_stats(self):
        # TODO(fbo)
        pass

    def test_extracts_cmts(self):
        # TODO(fbo)
        pass


class TestProjectIndexer(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.con = index.Connector(index='repoxplorertest')
        cls.cmts = commits.Commits(cls.con)
        indexer.conf['git_store'] = tempfile.mkdtemp()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(indexer.conf['git_store'])
        cls.con.ic.delete(index=cls.con.index)

    def test_init(self):
        pi = indexer.ProjectIndexer('p1', 'file:///tmp/p1', 'master')
        self.assertEqual(pi.project, 'file:///tmp/p1:p1:master')
        self.assertTrue(os.path.isdir(indexer.conf['git_store']))

    def test_index(self):
        pi = indexer.ProjectIndexer('p1', 'file:///tmp/p1',
                                    'master', con=self.con)
        pi.cmt_list_generator = \
            lambda sha_list, _: [c for c in repo_commits
                                 if c['sha'] in sha_list]

        # This is the initial commits list of a repository we
        # are going to index
        repo_commits = [
            {
                'sha': '3597334f2cb10772950c97ddf2f6cc17b184',
                'author_date': 1410456005,
                'committer_date': 1410456005,
                'author_name': 'Nakata Daisuke',
                'committer_name': 'Nakata Daisuke',
                'author_email': 'n.suke@joker.org',
                'committer_email': 'n.suke@joker.org',
                'projects': [
                    'file:///tmp/p1:p1:master', ],
                'line_modifieds': 10,
                'commit_msg': 'Add init method',
            },
        ]
        pi.commits = [rc['sha'] for rc in repo_commits]
        # Start the indexation
        pi.get_current_commit_indexed()
        pi.compute_to_index_to_delete()
        pi.index()
        # Check
        self.assertDictEqual(
            self.cmts.get_commits_by_id(pi.commits)['docs'][0]['_source'],
            repo_commits[0])
        self.assertEqual(
            len(self.cmts.get_commits_by_id(pi.commits)['docs']), 1)

        # The project evolves with an additional commit
        additional_cmt = {
            'sha': '3597334f2cb10772950c97ddf2f6cc17b185',
            'author_date': 1410456006,
            'committer_date': 1410456006,
            'author_name': 'Nakata Daisuke',
            'committer_name': 'Nakata Daisuke',
            'author_email': 'n.suke@joker.org',
            'committer_email': 'n.suke@joker.org',
            'projects': [
                'file:///tmp/p1:p1:master', ],
            'line_modifieds': 15,
            'commit_msg': 'Second commit',
        }
        repo_commits.append(additional_cmt)
        pi.commits = [rc['sha'] for rc in repo_commits]
        # Start the indexation
        pi.get_current_commit_indexed()
        pi.compute_to_index_to_delete()
        pi.index()
        # Check
        cmts = set([c['_source']['sha'] for c in
                    self.cmts.get_commits_by_id(pi.commits)['docs']])
        self.assertEqual(len(cmts), 2)
        cmts.difference_update(set([c['sha'] for c in repo_commits]))
        self.assertEqual(len(cmts), 0)

        # The project history has been rewritten
        repo_commits.pop()
        pi.commits = [rc['sha'] for rc in repo_commits]
        # Start the indexation
        pi.get_current_commit_indexed()
        pi.compute_to_index_to_delete()
        pi.index()
        # Check
        self.assertDictEqual(
            self.cmts.get_commits_by_id(pi.commits)['docs'][0]['_source'],
            repo_commits[0])
        self.assertEqual(
            len(self.cmts.get_commits_by_id(pi.commits)['docs']), 1)

        # Index p2 a fork of p1
        pi2 = indexer.ProjectIndexer('p2', 'file:///tmp/p2',
                                     'master', con=self.con)
        pi2.cmt_list_generator = \
            lambda sha_list, _: [c for c in repo2_commits
                                 if c['sha'] in sha_list]
        repo2_commits = [
            {
                'sha': '3597334f2cb10772950c97ddf2f6cc17b184',
                'author_date': 1410456005,
                'committer_date': 1410456005,
                'author_name': 'Nakata Daisuke',
                'committer_name': 'Nakata Daisuke',
                'author_email': 'n.suke@joker.org',
                'committer_email': 'n.suke@joker.org',
                'projects': [
                    'file:///tmp/p2:p2:master', ],
                'line_modifieds': 10,
                'commit_msg': 'Add init method',
            },
        ]
        pi2.commits = [rc['sha'] for rc in repo2_commits]
        # Start the indexation
        pi2.get_current_commit_indexed()
        pi2.compute_to_index_to_delete()
        pi2.index()
        # Check the commits has been marked belonging to both projects
        cmt = self.cmts.get_commit(repo2_commits[0]['sha'])
        self.assertIn('file:///tmp/p2:p2:master', cmt['projects'])
        self.assertIn('file:///tmp/p1:p1:master', cmt['projects'])

        # Add another commit with metadata extracted
        cmt = {
            'sha': '3597334f2cb10772950c97ddf2f6cc17b200',
            'author_date': 1410456005,
            'committer_date': 1410456005,
            'author_name': 'Nakata Daisuke',
            'committer_name': 'Nakata Daisuke',
            'author_email': 'n.suke@joker.org',
            'committer_email': 'n.suke@joker.org',
            'projects': [
                'file:///tmp/p2:p2:master', ],
            'line_modifieds': 10,
            'commit_msg': 'Add init method',
            'close-bug': '123',
            'related-to-story': '124',
        }
        repo2_commits.append(cmt)
        pi2.commits = [rc['sha'] for rc in repo2_commits]
        # Start the indexation
        pi2.get_current_commit_indexed()
        pi2.compute_to_index_to_delete()
        pi2.index()
        # Check the commits has been marked belonging to both projects
        cmt = self.cmts.get_commit(repo2_commits[1]['sha'])
        self.assertIn('close-bug', cmt)
        self.assertEqual(cmt['close-bug'], '123')
        self.assertIn('related-to-story', cmt)
        self.assertEqual(cmt['related-to-story'], '124')

    def test_index_tags(self):
        pi = indexer.ProjectIndexer('p1', 'file:///tmp/p1',
                                    'master', con=self.con)
        with mock.patch.object(indexer, 'run') as run:
            run.return_value = ['123\trefs/tags/t1\n124\trefs/tags/t2\n']
            pi.get_tags()
            self.assertListEqual(
                pi.tags, [['123', 'refs/tags/t1'], ['124', 'refs/tags/t2']])

        pi.cmt_list_generator = \
            lambda sha_list, _: [c for c in repo_commits
                                 if c['sha'] in sha_list]

        # This is the initial commits list of a repository we
        # are going to index
        repo_commits = [
            {
                'sha': '123',
                'author_date': 1410456005,
                'committer_date': 1410456005,
                'author_name': 'Nakata Daisuke',
                'committer_name': 'Nakata Daisuke',
                'author_email': 'n.suke@joker.org',
                'committer_email': 'n.suke@joker.org',
                'projects': [
                    'file:///tmp/p1:p1:master', ],
                'line_modifieds': 10,
                'commit_msg': 'Add init method',
            },
            {
                'sha': '124',
                'author_date': 1410456006,
                'committer_date': 1410456006,
                'author_name': 'Nakata Daisuke',
                'committer_name': 'Nakata Daisuke',
                'author_email': 'n.suke@joker.org',
                'committer_email': 'n.suke@joker.org',
                'projects': [
                    'file:///tmp/p1:p1:master', ],
                'line_modifieds': 10,
                'commit_msg': 'Add init method',
            },
        ]
        pi.commits = [rc['sha'] for rc in repo_commits]
        # Start the indexation
        pi.get_current_commit_indexed()
        pi.compute_to_index_to_delete()
        pi.index()
        # Start indexation of tags
        pi.index_tags()
        # Do it a second time
        pi.index_tags()

        tags = pi.t.get_tags(['file:///tmp/p1:p1:master'])

        t1 = [t['_source'] for t in tags if t['_source']['sha'] == '123'][0]
        self.assertEqual(t1['date'], 1410456005)
        self.assertEqual(t1['name'], 'refs/tags/t1')

        t2 = [t['_source'] for t in tags if t['_source']['sha'] == '124'][0]
        self.assertEqual(t2['date'], 1410456006)
        self.assertEqual(t2['name'], 'refs/tags/t2')
