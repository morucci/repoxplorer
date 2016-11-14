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
    return process.communicate()


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


def parse_commit_msg(msg):
    reserved_metadata_keys = PROPERTIES.keys()
    metadatas = {}
    lines = msg.split('\n')
    subject = lines[0].decode('utf-8', errors="replace")
    for line in lines[1:]:
        m = METADATA_RE.match(line)
        if m:
            key = m.groups()[0].decode('utf-8', errors="replace")
            if key not in reserved_metadata_keys:
                value = m.groups()[1].decode('utf-8', errors="replace")
                # Remove space before and after the string and remove
                # the \# that will cause trouble when metadata are queried
                # via the URL arguments
                metadatas[key.strip()] = value.strip().replace('#', '')
    return subject, metadatas


def extract_cmts(args):
    sha_list, path, project = args
    cmts = []
    logger.info("Worker start extracting %s commits" % len(sha_list))
    r = repo.Repo(path)
    for c, sha in enumerate(sha_list):
        if c % 250 == 0:
            logger.info("Worker %s remains %s commits to extract" % (
                mp.current_process(), len(sha_list) - c))
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
        subject, metadatas = parse_commit_msg(obj.message)
        source[u'commit_msg'] = subject
        source.update(metadatas)
        modified, merge_commit = get_diff_stats(r, obj)
        source[u'line_modifieds'] = modified
        source[u'merge_commit'] = merge_commit
        source[u'projects'] = [project, ]
        cmts.append(source)
    return cmts


class ProjectIndexer():
    def __init__(self, name, uri, branch, con=None, config=None):
        if not con:
            self.con = index.Connector()
        else:
            self.con = con
        self.c = Commits(self.con)
        if config:
            configuration.set_config(config)
        if not os.path.isdir(conf.git_store):
            os.makedirs(conf.git_store)
        self.name = name
        self.uri = uri
        self.branch = branch
        self.local = os.path.join(conf.git_store,
                                  self.name,
                                  self.uri.replace('/', '_'))
        if not os.path.isdir(self.local):
            os.makedirs(self.local)
        self.project = '%s:%s:%s' % (self.uri, self.name, self.branch)

    def __str__(self):
        return 'Git indexer of %s' % self.project

    def git_init(self):
        logger.info("Fetched %s %s:%s" % (self.name, self.uri,
                                          self.branch))
        with cdir(self.local):
            run("git init .")
            if "origin" not in run("git remote -v")[0]:
                run("git remote add origin %s" % self.uri)

    def git_fetch_branch(self):
        with cdir(self.local):
            run("git fetch origin %s" % self.branch)
        self.repo = repo.Repo(self.local)
        self.head = self.repo.get_refs()[
            'refs/remotes/origin/%s' % self.branch]

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
        """ Fetch from the index commits mentionned for this project
        and branch.
        """
        self.already_indexed = [c['_id'] for c in
                                self.c.get_commits(projects=[self.project],
                                                   scan=True)]
        logger.info(
            "In the DB - project history is composed of %s commits." % (
                len(self.already_indexed)))

    def compute_to_index_to_delete(self):
        """ Compute the list of commits (sha) to index and the
        list to delete from the index.
        """
        logger.info(
            "Upstream - project history is composed of %s commits." % (
                len(self.commits)))
        self.to_delete = set(self.already_indexed) - set(self.commits)
        self.to_index = set(self.commits) - set(self.already_indexed)
        logger.info(
            "Indexer will reference %s commits." % len(self.to_index))
        logger.info(
            "Indexer will dereference %s commits." % len(self.to_delete))

    def cmt_list_generator(self, sha_list, workers):
        if workers == 0:
            # Default value (auto)
            workers = mp.cpu_count() - 1 or 1
        elif workers == 1:
            return extract_cmts((sha_list, self.local, self.project))
        logger.info("Start commits extract with %s workers" % workers)
        worker_pool = mp.Pool(workers)
        sets = []
        set_lenght = len(sha_list) / workers
        for _ in xrange(workers - 1):
            sets.append((sha_list[:set_lenght], self.local, self.project))
            del sha_list[:set_lenght]
        sets.append((sha_list, self.local, self.project))
        extracted_sets = worker_pool.map(extract_cmts, sets)
        # TODO(fbo): Seems an issue exists here as childs should terminate
        # by themself
        worker_pool.terminate()
        worker_pool.join()
        ret = []
        for r in extracted_sets:
            ret.extend(r)
        return ret

    def index(self, extract_workers=1):
        # check whether a commit should be completly delete or
        # updated by removing the project from the projects field
        if self.to_delete:
            res = self.c.get_commits_by_id(list(self.to_delete))
            docs = [c['_source'] for
                    c in res['docs'] if c['found'] is True]
            to_delete = [c['sha'] for
                         c in docs if len(c['projects']) == 1]
            to_delete_update = [c['sha'] for
                                c in docs if len(c['projects']) > 1]

            logger.info("%s commits will be delete ..." % len(to_delete))
            self.c.del_commits(to_delete)

            logger.info("%s commits belonging to other projects "
                        "will be updated ..." % len(to_delete_update))
            res = self.c.get_commits_by_id(to_delete_update)
            if res:
                original_commits = [c['_source'] for
                                    c in res['docs']]
                for c in original_commits:
                    c['projects'].remove(self.project)
                self.c.update_commits(original_commits)

        # check whether a commit should be created or
        # updated by adding the project into the projects field
        if self.to_index:
            res = self.c.get_commits_by_id(list(self.to_index))
            to_update = [c['_source'] for
                         c in res['docs'] if c['found'] is True]
            to_create = [c['_id'] for
                         c in res['docs'] if c['found'] is False]
            logger.info("%s commits will be created ..." % len(to_create))
            self.c.add_commits(
                self.cmt_list_generator(to_create, extract_workers))

            logger.info(
                "%s commits already indexed and need to be updated" % (
                    len(to_update)))
            for c in to_update:
                c['projects'].append(self.project)
            self.c.update_commits(to_update)
