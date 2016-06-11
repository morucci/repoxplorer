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
                               shell=True)
    return process.communicate()


class ProjectIndexer():
    def __init__(self, name, uri, branch):
        self.con = index.Connector()
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

    def git_init(self):
        print "Fetched %s %s:%s" % (self.name, self.uri,
                                    self.branch)
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
            return modified
        if parents > 1:
            return 0

    def get_current_commit_indexed(self):
        """ Fetch from the index commits mentionned for this project
        and branch.
        """
        self.already_indexed = [c['_id'] for c in
                                self.c.get_commits(projects=[self.project],
                                                   scan=True)]
        print "Project history is composed of %s commits." % len(
            self.already_indexed)

    def compute_to_index_to_delete(self):
        """ Compute the list of commits (sha) to index and the
        list to delete from the index.
        """
        self.to_delete = set(self.already_indexed) - set(self.commits)
        self.to_index = set(self.commits) - set(self.already_indexed)
        print "Indexer will reference %s commits." % len(self.to_index)
        print "Indexer will dereference %s commits." % len(self.to_delete)

    def delete_from_index(self, sha, name, uri, branch):
        print "TODO dereference %s from %s:%s" % (sha, uri, branch)

    def add_into_index(self, sha):
        d = {}
        obj = self.repo.object_store[sha]
        d['author_date'] = obj.author_time
        d['committer_date'] = obj.commit_time
        d['sha'] = obj.id
        d['author_email'] = obj.author.split('<')[1].rstrip('>')
        d['author_name'] = obj.author.split('<')[0].rstrip()
        d['committer_email'] = obj.committer.split('<')[1].rstrip('>')
        d['committer_name'] = obj.committer.split('<')[0].rstrip()
        d['commit_msg'] = obj.message.split('\n', 1)[0]
        d['line_modifieds'] = self.get_diff_stats(obj)
        d['project'] = self.project
        self.c.add_commit(d)

    def bulk_index_generator(self, sha_list, index_name):
        for sha in sha_list:
            d = {}
            d['_index'] = index_name
            d['_op_type'] = 'create'
            d['_type'] = 'commits'
            d['_id'] = sha
            obj = self.repo.object_store[sha]
            source = {}
            source['author_date'] = obj.author_time
            source['committer_date'] = obj.commit_time
            source['sha'] = obj.id
            source['author_email'] = obj.author.split('<')[1].rstrip('>')
            source['author_name'] = obj.author.split('<')[0].rstrip()
            source['committer_email'] = obj.committer.split('<')[1].rstrip('>')
            source['committer_name'] = obj.committer.split('<')[0].rstrip()
            source['commit_msg'] = obj.message.split('\n', 1)[0]
            source['line_modifieds'] = self.get_diff_stats(obj)
            source['projects'] = [self.project, ]
            d['_source'] = source
            yield d

    def index(self):
        for to_delete in self.to_delete:
            self.delete_from_index(to_delete, self.name, self.uri, self.branch)
        stats = self.c.add_commits_bulk(
            self.bulk_index_generator(self.to_index, self.c.index))
        print "%s commits created" % stats[0]
        if stats[1]:
            # Expected errors and we want to update docs
            # This actual code is slow and need to be managed by
            # bulk (eg. fetch all existing commits, update them client side
            # then update by bulk.
            print "%s commits will be updated (slow)" % len(stats[1])
            for i in stats[1]:
                # Conflict SHA already indexed on another project or branch
                if i['create']['status'] == 409:
                    cid = i['create']['_id']
                    self.add_into_index(cid)
