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

from io import BytesIO

from dulwich import repo
from dulwich import patch

from repoxplorer import index
from repoxplorer.index.commits import Commits

REPOS_STORE = '/tmp/kmachine/repos_store'

RE_SOURCE_FILENAME = re.compile(
    r'^--- (?P<filename>[^\t\n]+)(?:\t(?P<timestamp>[^\n]+))?')
RE_TARGET_FILENAME = re.compile(
    r'^\+\+\+ (?P<filename>[^\t\n]+)(?:\t(?P<timestamp>[^\n]+))?')

logger = logging.getLogger('gitIndexer')


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


class ProjectIndexer():
    def __init__(self, name, uri, branch, con=None):
        if not con:
            self.con = index.Connector()
        else:
            self.con = con
        self.c = Commits(self.con)
        if not os.path.isdir(REPOS_STORE):
            os.makedirs(REPOS_STORE)
        self.name = name
        self.uri = uri
        self.branch = branch
        self.local = os.path.join(REPOS_STORE,
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

    def get_diff_stats(self, obj):
        parents = len(obj.parents)
        if parents <= 1:
            parent = getattr(obj, 'parents', None)
            if parent:
                parent = parent[0]
                parent_tree = self.repo.object_store[parent].tree
            else:
                parent_tree = None
            current_tree = obj.tree
            patch_content = BytesIO()
            patch.write_tree_diff(patch_content, self.repo.object_store,
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

    def cmt_list_generator(self, sha_list):
        # TODO: use multiprocessing here
        total = len(sha_list)
        consumed = 0
        for sha in sha_list:
            consumed += 1
            if consumed % 500 == 0:
                logger.info("indexing %s/%s ..." % (consumed, total))
            obj = self.repo.object_store[sha]
            source = {}
            source[u'author_date'] = obj.author_time
            source[u'committer_date'] = obj.commit_time
            source[u'sha'] = obj.id
            source[u'author_email'] = obj.author.split(
                '<')[1].rstrip('>')
            source[u'author_name'] = obj.author.split(
                '<')[0].rstrip().decode('utf-8')
            source[u'committer_email'] = obj.committer.split(
                '<')[1].rstrip('>')
            source[u'committer_name'] = obj.committer.split(
                '<')[0].rstrip().decode('utf-8')
            source[u'commit_msg'] = obj.message.split(
                '\n', 1)[0].decode('utf-8')
            modified, merge_commit = self.get_diff_stats(obj)
            source[u'line_modifieds'] = modified
            source[u'merge_commit'] = merge_commit
            source[u'projects'] = [self.project, ]
            yield source

    def index(self):
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
            self.c.add_commits(self.cmt_list_generator(to_create))

            logger.info(
                "%s commits already indexed and need to be updated" % (
                    len(to_update)))
            for c in to_update:
                c['projects'].append(self.project)
                self.c.update_commits(to_update)
