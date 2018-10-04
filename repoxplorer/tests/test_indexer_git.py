import os
import re
import mock
import shutil
import cPickle
import tempfile

from unittest import TestCase
from mock import patch

from repoxplorer import index
from repoxplorer.index import commits
from repoxplorer.index import projects
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
            raw, ['file:///gitshow.sample'])
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
             'files_list': [
                 'modules',
                 'modules/openstack_project',
                 'modules/openstack_project/files',
                 'modules/openstack_project/files/puppetmaster',
                 'modules/openstack_project/files/puppetmaster/mqtt.py'],
             u'Change-Id': [
                 u'I3e6240560ad562e8f41f7e314ef7a4b0b1178e32'],
             'author_name': u'Author A',
             'committer_name': u'Author A',
             'author_email': 'author.a@test',
             'author_email_domain': 'test'},
            {'ttl': 0,
             'line_modifieds': 0,
             'commit_msg': u'Merge "Cast the playbook uuid as a string"',
             'sha': '0e58c2fd54a50362138849a20bced510480dac8d',
             'repos': ['file:///gitshow.sample'],
             'merge_commit': True,
             'committer_date': 1493423272,
             'author_date': 1493423272,
             'committer_email': 'review@openstack.org',
             'files_list': [],
             'author_name': u'Jenkins',
             'committer_name': u'Gerrit Code Review',
             'author_email': 'jenkins@review.openstack.org',
             'author_email_domain': 'review.openstack.org'},
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
             'files_list': [],
             'author_name': u'Jenkins',
             'committer_name': u'Gerrit Code Review',
             'author_email': 'jenkins@review.openstack.org',
             'author_email_domain': 'review.openstack.org'},
            {'ttl': 1651141,
             'line_modifieds': 64,
             'commit_msg': u'Add firehose schema docs',
             'sha': 'd9fda5b81f6c8d64fda2ca2c08246492e800292f',
             'repos': ['file:///gitshow.sample'],
             'merge_commit': False,
             'committer_date': 1493244209,
             'author_date': 1491593068,
             'committer_email': 'author.b@test',
             u'Change-Id': [u'I2157f702c87f32055ba2fad842a05e31539bc857'],
             'files_list': [
                 'doc',
                 'doc/source',
                 'doc/source/components.rst',
                 'doc/source/firehose.rst',
                 'doc/source/firehose_schema.rst',
                 'doc/source/systems.rst'],
             'author_name': u'Author A',
             'committer_name': u'Author B',
             'author_email': 'author.a@test',
             'author_email_domain': 'test'},
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
             'files_list': [
                 'modules',
                 'modules/openstack_project',
                 'modules/openstack_project/templates',
                 'modules/openstack_project/templates/logstash',
                 'modules/openstack_project/templates/logstash/' +
                 'jenkins-subunit-worker.yaml.erb'],
             'author_name': u'Author C',
             'committer_name': u'Author C',
             'author_email': 'author.c@test',
             'author_email_domain': 'test'},
            {'author_date': 1493240029,
             'author_email': u'author.c@test',
             'author_email_domain': u'test',
             'author_name': u'Author C',
             'commit_msg': u'Add type declarations for Windows API calls as '
             'found in jaraco.windows 3.6.1. Fixes #758.',
             'committer_date': 1493240029,
             'committer_email': u'author.c@test',
             'committer_name': u'Author C',
             'files_list': [
                 'paramiko',
                 'paramiko/_winapi.py',
                 'sites',
                 'sites/www',
                 'sites/www/changelog.rst'],
             'line_modifieds': 21,
             'merge_commit': False,
             'repos': ['file:///gitshow.sample'],
             'sha': '88364beba125cc8e6e314885db1c909b3d526340',
             'ttl': 0},
            {'author_date': 1493240029,
             'author_email': u'author.c@test',
             'author_email_domain': u'test',
             'author_name': u'Author C',
             'commit_msg': u'windows linefeed was breaking /usr/bin/env from '
             'executing correctly :/s/',
             'committer_date': 1493240029,
             'committer_email': u'author.c@test',
             'committer_name': u'Author C',
             'line_modifieds': 2,
             'merge_commit': False,
             'files_list': ['SickBeard.py'],
             'repos': ['file:///gitshow.sample'],
             'sha': 'f5d7eb5b623b625062cf0d3d8d552ee0ea9000dd',
             'ttl': 0},
            {'author_date': 1493240029,
             'author_email': u'author.c@test',
             'author_email_domain': u'test',
             'author_name': u'Author C',
             'commit_msg': u'Merge pull request #13155 from '
             'coolljt0725/fix_validate_tag_name',
             'committer_date': 1493240029,
             'committer_email': u'author.c@test',
             'committer_name': u'Author C',
             'line_modifieds': 0,
             'files_list': [],
             'merge_commit': True,
             'repos': ['file:///gitshow.sample'],
             'sha': '8e1cc08e799a83ace198ee7a3c6f9169635e7f46',
             'ttl': 0},
            {'author_date': 1352117713,
             'author_email': u'',
             'author_email_domain': u'',
             'author_name': u'mysql-builder@oracle.com',
             'commit_msg': '',
             'committer_date': 1352117713,
             'committer_email': u'',
             'committer_name': u'mysql-builder@oracle.com',
             'files_list': [],
             'line_modifieds': 0,
             'merge_commit': False,
             'repos': ['file:///gitshow.sample'],
             'sha': '1c939e7487986f1ada02f1414f6101b7cd696824',
             'ttl': 0},
            ]

        self.assertListEqual(output, expected)


class TestRefsClean(TestCase):

    @classmethod
    def setUpClass(cls):
        indexer.conf['git_store'] = tempfile.mkdtemp()
        indexer.conf['db_path'] = tempfile.mkdtemp()
        indexer.conf['elasticsearch_index'] = 'repoxplorertest'
        indexer.get_commits_desc = lambda path, shas: []
        cls.con = index.Connector()
        cls.cmts = commits.Commits(cls.con)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(indexer.conf['git_store'])
        shutil.rmtree(indexer.conf['db_path'])
        cls.con.ic.delete(index=cls.con.index)

    def setUp(self):
        self.seen_refs = os.path.join(
            indexer.conf['db_path'], indexer.SEEN_REFS_CACHED)
        if os.path.isfile(self.seen_refs):
            os.unlink(self.seen_refs)

    def tearDown(self):
        os.unlink(self.seen_refs)

    def init_fake_process_commits_desc_output(self, pi, repo_commits):
        to_create, _ = pi.compute_to_create_to_update()
        to_create = [
            c for c in repo_commits if c['sha'] in to_create]
        indexer.process_commits_desc_output = lambda buf, ref_id: to_create

    def test_cleaner(self):
        pi = indexer.RepoIndexer('p1', 'file:///tmp/p1',
                                 con=self.con)
        # This is the initial commits list of a repository we
        # are going to index
        repo_commits1 = [
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
        pi.commits = [rc['sha'] for rc in repo_commits1]
        pi.set_branch('master')
        # Start the indexation
        pi.get_current_commit_indexed()
        pi.compute_to_index_to_delete()
        self.init_fake_process_commits_desc_output(pi, repo_commits1)
        pi.index()
        repo_commits2 = [
            {
                'sha': '3597334f2cb10772950c97ddf2f6cc17b185',
                'author_date': 1410456005,
                'committer_date': 1410456005,
                'author_name': 'Nakata Daisuke',
                'committer_name': 'Nakata Daisuke',
                'author_email': 'n.suke@joker.org',
                'committer_email': 'n.suke@joker.org',
                'repos': [
                    'file:///tmp/p1:p1:devel', 'meta_ref: Fedora'],
                'line_modifieds': 10,
                'commit_msg': 'Add init method',
            },
            {
                'sha': '3597334f2cb10772950c97ddf2f6cc17b186',
                'author_date': 1410456005,
                'committer_date': 1410456005,
                'author_name': 'Nakata Daisuke',
                'committer_name': 'Nakata Daisuke',
                'author_email': 'n.suke@joker.org',
                'committer_email': 'n.suke@joker.org',
                'repos': [
                    'file:///tmp/p1:p1:devel',
                    'file:///tmp/p1:p1:master',
                    'meta_ref: Fedora'],
                'line_modifieds': 10,
                'commit_msg': 'Add init method',
            },
        ]
        pi.commits = [rc['sha'] for rc in repo_commits2]
        pi.set_branch('devel')
        # Start the indexation
        pi.get_current_commit_indexed()
        pi.compute_to_index_to_delete()
        self.init_fake_process_commits_desc_output(pi, repo_commits2)
        pi.index()

        shas = ['3597334f2cb10772950c97ddf2f6cc17b184',
                '3597334f2cb10772950c97ddf2f6cc17b185',
                '3597334f2cb10772950c97ddf2f6cc17b186']

        pi.tags = [['3597334f2cb10772950c97ddf2f6cc17b184', 'refs/tags/t1'],
                   ['3597334f2cb10772950c97ddf2f6cc17b185', 'refs/tags/t2']]
        pi.index_tags()
        self.assertEqual(len(pi.t.get_tags(['file:///tmp/p1:p1'])), 2)

        # Check 3 commits are indexed
        self.assertEqual(
            len([c for c in self.cmts.get_commits_by_id(shas)['docs']
                 if c['found']]), 3)

        # Now create the RefsCleaner instance
        # '3597334f2cb10772950c97ddf2f6cc17b185' will be removed
        # '3597334f2cb10772950c97ddf2f6cc17b186' will be updated
        # as the devel branch is no longer referenced
        with patch.object(index.YAMLBackend, 'load_db'):
            with patch.object(projects.Projects, 'get_projects_raw') as gpr:
                projects_index = projects.Projects('/tmp/fakepath')
                gpr.return_value = {
                    'p1': {
                        'repos': {
                            'p1': {
                                'branches': ['master'],
                                'uri': 'file:///tmp/p1',
                                }
                            }
                        }
                    }
                rc = indexer.RefsCleaner(projects_index, con=self.con)
                refs_to_clean = rc.find_refs_to_clean()
                rc.clean(refs_to_clean)
        # Two commits must be in the db (two was from the master branch)
        cmts = self.cmts.get_commits_by_id(shas)['docs']
        self.assertEqual(len([c for c in cmts if c['found']]), 2)
        # Verify that remaining commits belong to ref
        # 'file:///tmp/p1:p1:master' only
        for cmt in cmts:
            if not cmt['found']:
                continue
            self.assertIn(
                'file:///tmp/p1:p1:master', cmt['_source']['repos'])
            self.assertNotIn(
                'file:///tmp/p1:p1:devel', cmt['_source']['repos'])

        # Here make sure tags are still reference as the base_id still exists
        self.assertEqual(len(pi.t.get_tags(['file:///tmp/p1:p1'])), 2)
        # Reinstance a RefsCleaner with no repos
        with patch.object(index.YAMLBackend, 'load_db'):
            with patch.object(projects.Projects, 'get_projects_raw') as gpr:
                projects_index = projects.Projects('/tmp/fakepath')
                gpr.return_value = {
                    'p1': {
                        'repos': {}
                        }
                    }
                rc = indexer.RefsCleaner(projects_index, con=self.con)
                refs_to_clean = rc.find_refs_to_clean()
                rc.clean(refs_to_clean)
        # Make sure tags have been deleted
        self.assertEqual(len(pi.t.get_tags(['file:///tmp/p1:p1'])), 0)


class TestRepoIndexer(TestCase):

    @classmethod
    def setUpClass(cls):
        indexer.conf['git_store'] = tempfile.mkdtemp()
        indexer.conf['db_path'] = tempfile.mkdtemp()
        indexer.conf['elasticsearch_index'] = 'repoxplorertest'
        indexer.get_commits_desc = lambda path, shas: []
        cls.con = index.Connector()
        cls.cmts = commits.Commits(cls.con)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(indexer.conf['git_store'])
        shutil.rmtree(indexer.conf['db_path'])
        cls.con.ic.delete(index=cls.con.index)

    def setUp(self):
        self.seen_refs = os.path.join(
            indexer.conf['db_path'], indexer.SEEN_REFS_CACHED)
        if os.path.isfile(self.seen_refs):
            os.unlink(self.seen_refs)

    def tearDown(self):
        os.unlink(self.seen_refs)

    def init_fake_process_commits_desc_output(self, pi, repo_commits):
        to_create, _ = pi.compute_to_create_to_update()
        to_create = [
            c for c in repo_commits if c['sha'] in to_create]
        indexer.process_commits_desc_output = lambda buf, ref_id: to_create

    def test_init(self):
        pi = indexer.RepoIndexer('p1', 'file:///tmp/p1')
        pi.set_branch('master')
        self.assertEqual(pi.ref_id, 'file:///tmp/p1:p1:master')
        self.assertTrue(os.path.isdir(indexer.conf['git_store']))
        seen_refs = cPickle.load(file(self.seen_refs))
        self.assertTrue(len(seen_refs), 1)
        self.assertIn('file:///tmp/p1:p1:master', seen_refs)

    def test_init_with_meta_ref(self):
        pi = indexer.RepoIndexer('p1', 'file:///tmp/p1', meta_ref='Fedora')
        pi.set_branch('master')
        self.assertEqual(pi.ref_id, 'file:///tmp/p1:p1:master')
        self.assertEqual(pi.meta_ref, 'meta-ref: Fedora')
        self.assertTrue(os.path.isdir(indexer.conf['git_store']))
        seen_refs = cPickle.load(file(self.seen_refs))
        # The meta-ref is not added to seen refs store
        self.assertTrue(len(seen_refs), 1)
        self.assertIn('file:///tmp/p1:p1:master', seen_refs)

    def test_index(self):
        pi = indexer.RepoIndexer('p1', 'file:///tmp/p1',
                                 con=self.con)

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
        self.init_fake_process_commits_desc_output(pi, repo_commits)
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
        self.init_fake_process_commits_desc_output(pi, repo_commits)
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
        self.init_fake_process_commits_desc_output(pi, repo_commits)
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
        self.init_fake_process_commits_desc_output(pi2, repo2_commits)
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
        self.init_fake_process_commits_desc_output(pi2, repo2_commits)
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
        to_create, _ = pi.compute_to_create_to_update()
        to_create = [
            c for c in repo_commits if c['sha'] in to_create]
        indexer.process_commits_desc_output = lambda buf, ref_id: to_create
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
