# Copyright 2016, Fabien Boucher
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.


import os
import re
import copy
import logging
import contextlib
import subprocess
import multiprocessing as mp

from io import BytesIO

from pecan import configuration
from pecan import conf

from dulwich import repo
from dulwich import patch

from repoxplorer import index
from repoxplorer.index.commits import Commits
from repoxplorer.index.commits import PROPERTIES
from repoxplorer.index.tags import Tags


RE_SOURCE_FILENAME = re.compile(
    r'^--- (?P<filename>[^\t\n]+)(?:\t(?P<timestamp>[^\n]+))?')
RE_TARGET_FILENAME = re.compile(
    r'^\+\+\+ (?P<filename>[^\t\n]+)(?:\t(?P<timestamp>[^\n]+))?')
METADATA_RE = re.compile('^([a-zA-Z-0-9_-]+):([^//].+)$')

logger = logging.getLogger(__name__)


@contextlib.contextmanager
def cdir(path):
    prev_cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_cwd)


def run(cmd):
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               shell=True)
    out = process.communicate()
    if process.returncode != 0:
        raise Exception('%s exited with code %s' % (cmd, process.returncode))
    return out


def get_diff_stats(r, obj):
    parents = len(obj.parents)
    if parents <= 1:
        parent = getattr(obj, 'parents', None)
        if parent:
            parent = parent[0]
            parent_tree = r.object_store[parent].tree
        else:
            parent_tree = None
        current_tree = obj.tree
        patch_content = BytesIO()
        patch.write_tree_diff(patch_content, r.object_store,
                              parent_tree, current_tree)
        patch_content.seek(0)
        content = patch_content.readlines()
        modified = 0
        for line in content:
            if RE_SOURCE_FILENAME.match(line):
                continue
            if RE_TARGET_FILENAME.match(line):
                continue
            if line[0] == '+' or line[0] == '-':
                modified += 1
        return modified, False
    if parents > 1:
        return 0, True


def parse_commit_line(line, re):
    reserved_metadata_keys = PROPERTIES.keys()
    m = re.match(line)
    if m:
        key = m.groups()[0].decode('utf-8', errors="replace")
        if key not in reserved_metadata_keys:
            value = m.groups()[1].decode('utf-8', errors="replace")
            # Remove space before and after the string and remove
            # the \# that will cause trouble when metadata are queried
            # via the URL arguments
            return key.strip(), value.strip().replace('#', '')


def parse_commit_msg(msg, extra_parsers=None):
    metadatas = []
    parsers = [METADATA_RE, ]
    if extra_parsers:
        for p in extra_parsers:
            parsers.append(p)
    lines = msg.split('\n')
    subject = lines[0].decode('utf-8', errors="replace")
    for line in lines[1:]:
        for parser in parsers:
            metadata = parse_commit_line(line, parser)
            if metadata:
                metadatas.append(metadata)
    return subject, metadatas


def extract_cmts(args):
    sha_list, path, repo_name, extra_parsers = args
    name = repo_name.split(':')[-2]
    cmts = []
    logger.debug("%s: Worker start extracting %s commits" % (
        name, len(sha_list)))
    r = repo.Repo(path)
    for c, sha in enumerate(sha_list):
        if c % 500 == 0:
            logger.info("%s: Worker %s remains %s commits to extract" % (
                name, mp.current_process(), len(sha_list) - c))
        obj = r.object_store[sha]
        source = {}
        source[u'author_date'] = obj.author_time
        source[u'committer_date'] = obj.commit_time
        source[u'ttl'] = int(obj.commit_time - obj.author_time)
        source[u'sha'] = obj.id
        source[u'author_email'] = obj.author.split(
            '<')[1].rstrip('>')
        source[u'committer_email'] = obj.committer.split(
            '<')[1].rstrip('>')
        source[u'author_name'] = obj.author.split(
            '<')[0].rstrip().decode('utf-8', errors="replace")
        source[u'committer_name'] = obj.committer.split(
            '<')[0].rstrip().decode('utf-8', errors="replace")
        subject, metadatas = parse_commit_msg(obj.message, extra_parsers)
        source[u'commit_msg'] = subject
        for metadata in metadatas:
            if metadata[0] not in source:
                source[metadata[0]] = []
            source[metadata[0]].append(metadata[1])
        modified, merge_commit = get_diff_stats(r, obj)
        source[u'line_modifieds'] = modified
        source[u'merge_commit'] = merge_commit
        source[u'repos'] = [repo_name, ]
        cmts.append(source)
    return cmts


class RepoIndexer():
    def __init__(self, name, uri, branch, parsers=None,
                 con=None, config=None):
        if config:
            configuration.set_config(config)
        if not con:
            self.con = index.Connector()
        else:
            self.con = con
        self.c = Commits(self.con)
        self.t = Tags(self.con)
        if not os.path.isdir(conf.git_store):
            os.makedirs(conf.git_store)
        self.name = name
        self.uri = uri
        self.branch = branch
        if not parsers:
            self.parsers = []
        else:
            self.parsers = parsers
        self.local = os.path.join(conf.git_store,
                                  self.name,
                                  self.uri.replace('/', '_'))
        if not os.path.isdir(self.local):
            os.makedirs(self.local)
        self.repo_id = '%s:%s:%s' % (self.uri, self.name, self.branch)

    def __str__(self):
        return 'Git indexer of %s' % self.repo_id

    def git_init(self):
        logger.debug("Fetch %s %s:%s" % (self.name, self.uri,
                                         self.branch))
        with cdir(self.local):
            run("git init .")
            if "origin" not in run("git remote -v")[0]:
                run("git remote add origin %s" % self.uri)

    def git_fetch_branch(self):
        with cdir(self.local):
            run("git fetch origin %s" % self.branch)
            self.head = run("git rev-parse FETCH_HEAD")[0].strip()
        self.repo = repo.Repo(self.local)

    def get_tags(self):
        with cdir(self.local):
            _refs = run("git ls-remote origin")[0].split('\n')
            del _refs[-1]
            refs = []
            for r in _refs:
                refs.append(r.split('\t'))
            self.tags = filter(lambda x: x[1].startswith('refs/tags') and
                               not x[1].endswith('^{}'), refs)

    def git_get_commit_obj(self):
        commits = {}
        to_consume = [self.head]
        while to_consume:
            n = to_consume.pop()
            nexts = self.repo.get_parents(n)
            commits[n] = None
            for n in nexts:
                if n not in commits.keys():
                    to_consume.append(n)
        self.commits = commits.keys()

    def get_current_commit_indexed(self):
        """ Fetch from the index commits mentionned for this repo
        and branch.
        """
        self.already_indexed = [c['_id'] for c in
                                self.c.get_commits(repos=[self.repo_id],
                                                   scan=True)]
        logger.debug(
            "%s: In the DB - repo history is composed of %s commits." % (
                self.name, len(self.already_indexed)))

    def compute_to_index_to_delete(self):
        """ Compute the list of commits (sha) to index and the
        list to delete from the index.
        """
        logger.debug(
            "%s: Upstream - repo history is composed of %s commits." % (
                self.name, len(self.commits)))
        self.to_delete = set(self.already_indexed) - set(self.commits)
        self.to_index = set(self.commits) - set(self.already_indexed)
        logger.debug(
            "%s: Indexer will reference %s commits." % (
                self.name,
                len(self.to_index)))
        logger.debug(
            "%s: Indexer will dereference %s commits." % (
                self.name,
                len(self.to_delete)))

    def cmt_list_generator(self, sha_list, workers):
        if workers == 0:
            # Default value (auto)
            workers = mp.cpu_count() - 1 or 1
        elif workers == 1:
            return extract_cmts((sha_list, self.local,
                                 self.repo_id, self.parsers))
        logger.debug("%s: Start commits extract with %s workers" % (
            self.name, workers))
        worker_pool = mp.Pool(workers)
        sets = []
        set_length = len(sha_list) / workers
        for _ in xrange(workers - 1):
            sets.append((sha_list[:set_length], self.local,
                         self.repo_id, self.parsers))
            del sha_list[:set_length]
        sets.append((sha_list, self.local,
                     self.repo_id, self.parsers))
        extracted_sets = worker_pool.map(extract_cmts, sets)
        # TODO(fbo): Seems an issue exists here as childs should terminate
        # by themself
        worker_pool.terminate()
        worker_pool.join()
        ret = []
        for r in extracted_sets:
            ret.extend(r)
        return ret

    def index_tags(self):
        def c_tid(t):
            return "%s%s%s" % (t['sha'],
                               t['name'].replace('refs/tags/', ''),
                               t['repo'])
        if not self.tags:
            logger.debug('%s: no tags detected for this repository' % (
                         self.name))
            return
        logger.debug('%s: %s tags exist upstream' % (
                     self.name, len(self.tags)))
        tags = self.t.get_tags([self.repo_id])
        existing = dict([(c_tid(t['_source']), t['_id']) for t in tags])
        logger.debug('%s: %s tags already referenced' % (
                     self.name, len(existing)))
        # Some commits may be not found because it is possible the branches
        # has not been indexed In that case the _source key won't exist
        commits = [c['_source'] for c in self.c.get_commits_by_id(
                   [t[0] for t in self.tags])['docs'] if c and '_source' in c]
        lookup = dict([(c['sha'], c['committer_date']) for c in commits])
        to_delete = [v for k, v in existing.items() if
                     k not in ["%s%s%s" % (sha,
                                           name.replace('refs/tags/', ''),
                                           self.repo_id) for
                               sha, name in self.tags]]
        docs = []
        for sha, name in self.tags:
            if sha in lookup:
                doc = {}
                doc['name'] = name.replace('refs/tags/', '')
                doc['sha'] = sha
                doc['date'] = lookup[sha]
                doc['repo'] = self.repo_id
                if c_tid(doc) in existing:
                    continue
                docs.append(doc)
        if docs:
            logger.info('%s: %s tags will be indexed' % (
                        self.name, len(docs)))
            self.t.add_tags(docs)
        if to_delete:
            logger.info('%s: %s tags will be deleted' % (
                        self.name, len(to_delete)))
            self.t.del_tags(to_delete)

    def index(self, extract_workers=1):
        # Compile the parsers
        if self.parsers:
            raw_parsers = copy.deepcopy(self.parsers)
            self.parsers = []
            for parser in raw_parsers:
                self.parsers.append(re.compile(parser))
            logger.debug("%s: Prepared %s regex parsers for commit msgs" % (
                self.name, len(self.parsers)))
        # check whether a commit should be completly deleted or
        # updated by removing the repo from the repos field
        if self.to_delete:
            res = self.c.get_commits_by_id(list(self.to_delete))
            docs = [c['_source'] for
                    c in res['docs'] if c['found'] is True]
            to_delete = [c['sha'] for
                         c in docs if len(c['repos']) == 1]
            to_delete_update = [c['sha'] for
                                c in docs if len(c['repos']) > 1]

            logger.info("%s: %s commits will be delete ..." % (
                self.name, len(to_delete)))
            self.c.del_commits(to_delete)

            logger.info("%s: %s commits belonging to other repos "
                        "will be updated ..." % (
                            self.name, len(to_delete_update)))
            res = self.c.get_commits_by_id(to_delete_update)
            if res:
                original_commits = [c['_source'] for
                                    c in res['docs']]
                for c in original_commits:
                    c['repos'].remove(self.repo_id)
                self.c.update_commits(original_commits)

        # check whether a commit should be created or
        # updated by adding the repo into the repos field
        if self.to_index:
            res = self.c.get_commits_by_id(list(self.to_index))
            to_update = [c['_source'] for
                         c in res['docs'] if c['found'] is True]
            to_create = [c['_id'] for
                         c in res['docs'] if c['found'] is False]
            logger.info("%s: %s commits will be created ..." % (
                self.name, len(to_create)))
            self.c.add_commits(
                self.cmt_list_generator(to_create, extract_workers))

            logger.info(
                "%s: %s commits already indexed and need to be updated" % (
                    self.name, len(to_update)))
            for c in to_update:
                c['repos'].append(self.repo_id)
            self.c.update_commits(to_update)
