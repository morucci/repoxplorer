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

    def setUp(self):
        self.maxDiff = None

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

    def test_parse_commit_desc_output(self):
        cd = os.path.dirname(os.path.realpath(__file__))
        raw = file(
            os.path.join(cd, 'gitshow.sample')).read().splitlines()
        output = indexer.process_commits_desc_output(
            raw, 'file:///gitshow.sample')
        expected = [
            {'ttl': 487,
             'line_modifieds': 10,
             'commit_msg': u'Make playbook and task in topic singular',
             'sha': '1ef6088bb6678b78993672ffdec93c7c99a0405d',
             'repos': ['file:///gitshow.sample'],
             'merge_commit': False,
             'committer_date': 1493425136,
             'author_date': 1493424649,
             'committer_email': 'author.a@test',
             u'Change-Id': [
                 u'I3e6240560ad562e8f41f7e314ef7a4b0b1178e32'],
             'author_name': u'Author A',
             'committer_name': u'Author A',
             'author_email': 'author.a@test'},
            {'ttl': 0,
             'line_modifieds': 0,
             'commit_msg': u'Merge "Cast the playbook uuid as a string"',
             'sha': '0e58c2fd54a50362138849a20bced510480dac8d',
             'repos': ['file:///gitshow.sample'],
             'merge_commit': True,
             'committer_date': 1493423272,
             'author_date': 1493423272,
             'committer_email': 'review@openstack.org',
             'author_name': u'Jenkins',
             'committer_name': u'Gerrit Code Review',
             'author_email': 'jenkins@review.openstack.org'},
            {'ttl': 0,
             'line_modifieds': 0,
             'commit_msg': u'Merge "Add subunit gearman worker '
             'mqtt info to firehose docs"',
             'sha': 'fb7d2712a907f8f01b817889e88abaf0dad6a109',
             'repos': ['file:///gitshow.sample'],
             'merge_commit': True,
             'committer_date': 1493413511,
             'author_date': 1493413511,
             'committer_email': 'review@openstack.org',
             'author_name': u'Jenkins',
             'committer_name': u'Gerrit Code Review',
             'author_email': 'jenkins@review.openstack.org'},
            {'ttl': 1651141,
             'line_modifieds': 61,
             'commit_msg': u'Add firehose schema docs',
             'sha': 'd9fda5b81f6c8d64fda2ca2c08246492e800292f',
             'repos': ['file:///gitshow.sample'],
             'merge_commit': False,
             'committer_date': 1493244209,
             'author_date': 1491593068,
             'committer_email': 'author.b@test',
             u'Change-Id': [u'I2157f702c87f32055ba2fad842a05e31539bc857'],
             'author_name': u'Author A',
             'committer_name': u'Author B',
             'author_email': 'author.a@test'},
            {'ttl': 0,
             'line_modifieds': 2,
             'commit_msg': u'Fix use of _ that should be - in mqtt-ca_certs',
             'sha': '8cb34d026e9c290b83c52301d82b2011406fc7d8',
             'repos': ['file:///gitshow.sample'],
             'merge_commit': False,
             'committer_date': 1493240029,
             'author_date': 1493240029,
             'committer_email': 'author.c@test',
             u'Change-Id': [u'I4155bdd80523b73fdc69f45d6120e8eec986dda7'],
             'author_name': u'Author C',
             'committer_name': u'Author C',
             'author_email': 'author.c@test'},
            {'author_date': 1493240029,
             'author_email': u'author.c@test',
             'author_name': u'Author C',
             'commit_msg': u'Merge pull request #13155 from '
             'coolljt0725/fix_validate_tag_name',
             'committer_date': 1493240029,
             'committer_email': u'author.c@test',
             'committer_name': u'Author C',
             'line_modifieds': 0,
             'merge_commit': True,
             'repos': ['file:///gitshow.sample'],
             'sha': '8e1cc08e799a83ace198ee7a3c6f9169635e7f46',
             'ttl': 0}]

        self.assertListEqual(output, expected)


class TestRepoIndexer(TestCase):

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
        pi = indexer.RepoIndexer('p1', 'file:///tmp/p1')
        pi.set_branch('master')
        self.assertEqual(pi.ref_id, 'file:///tmp/p1:p1:master')
        self.assertTrue(os.path.isdir(indexer.conf['git_store']))

    def test_index(self):
        pi = indexer.RepoIndexer('p1', 'file:///tmp/p1',
                                 con=self.con)
        pi.run_workers = \
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
                'repos': [
                    'file:///tmp/p1:p1:master', ],
                'line_modifieds': 10,
                'commit_msg': 'Add init method',
            },
        ]
        pi.commits = [rc['sha'] for rc in repo_commits]
        pi.set_branch('master')
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

        # The repo evolves with an additional commit
        additional_cmt = {
            'sha': '3597334f2cb10772950c97ddf2f6cc17b185',
            'author_date': 1410456006,
            'committer_date': 1410456006,
            'author_name': 'Nakata Daisuke',
            'committer_name': 'Nakata Daisuke',
            'author_email': 'n.suke@joker.org',
            'committer_email': 'n.suke@joker.org',
            'repos': [
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

        # The repo history has been rewritten
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
        pi2 = indexer.RepoIndexer('p2', 'file:///tmp/p2',
                                  con=self.con)
        pi2.run_workers = \
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
                'repos': [
                    'file:///tmp/p2:p2:master', ],
                'line_modifieds': 10,
                'commit_msg': 'Add init method',
            },
        ]
        pi2.commits = [rc['sha'] for rc in repo2_commits]
        pi2.set_branch('master')
        # Start the indexation
        pi2.get_current_commit_indexed()
        pi2.compute_to_index_to_delete()
        pi2.index()
        # Check the commits has been marked belonging to both repos
        cmt = self.cmts.get_commit(repo2_commits[0]['sha'])
        self.assertIn('file:///tmp/p2:p2:master', cmt['repos'])
        self.assertIn('file:///tmp/p1:p1:master', cmt['repos'])

        # Add another commit with metadata extracted
        cmt = {
            'sha': '3597334f2cb10772950c97ddf2f6cc17b200',
            'author_date': 1410456005,
            'committer_date': 1410456005,
            'author_name': 'Nakata Daisuke',
            'committer_name': 'Nakata Daisuke',
            'author_email': 'n.suke@joker.org',
            'committer_email': 'n.suke@joker.org',
            'repos': [
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
        # Check the commits has been marked belonging to both repos
        cmt = self.cmts.get_commit(repo2_commits[1]['sha'])
        self.assertIn('close-bug', cmt)
        self.assertEqual(cmt['close-bug'], '123')
        self.assertIn('related-to-story', cmt)
        self.assertEqual(cmt['related-to-story'], '124')

    def test_index_tags(self):
        pi = indexer.RepoIndexer('p1', 'file:///tmp/p1',
                                 con=self.con)
        with mock.patch.object(indexer, 'run') as run:
            run.return_value = "123\trefs/tags/t1\n124\trefs/tags/t2\n"
            pi.get_refs()
            pi.get_tags()
            self.assertListEqual(
                pi.tags, [['123', 'refs/tags/t1'], ['124', 'refs/tags/t2']])

        pi.run_workers = \
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
                'repos': [
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
                'repos': [
                    'file:///tmp/p1:p1:master', ],
                'line_modifieds': 10,
                'commit_msg': 'Add init method',
            },
        ]
        pi.commits = [rc['sha'] for rc in repo_commits]
        pi.set_branch('master')
        # Start the indexation
        pi.get_current_commit_indexed()
        pi.compute_to_index_to_delete()
        pi.index()
        # Start indexation of tags
        pi.index_tags()
        # Do it a second time
        pi.index_tags()

        tags = pi.t.get_tags(['file:///tmp/p1:p1'])

        t1 = [t['_source'] for t in tags if t['_source']['sha'] == '123'][0]
        self.assertEqual(t1['date'], 1410456005)
        self.assertEqual(t1['name'], 't1')

        t2 = [t['_source'] for t in tags if t['_source']['sha'] == '124'][0]
        self.assertEqual(t2['date'], 1410456006)
        self.assertEqual(t2['name'], 't2')
