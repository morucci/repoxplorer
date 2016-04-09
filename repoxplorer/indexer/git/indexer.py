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
        print "Indexer will index %s commits." % len(self.to_index)
        print "Indexer will delete %s commits." % len(self.to_delete)

    def delete_from_index(self, sha, name, uri, branch):
        print "TODO: Deleting %s from %s:%s" % (sha, uri, branch)

    def add_into_index(self, sha, name, uri, branch):
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
        d['line_modified'] = self.get_diff_stats(obj)
        d['project'] = self.project
        self.c.add_commit(d)

    def index(self):
        for to_delete in self.to_delete:
            self.delete_from_index(to_delete, self.name, self.uri, self.branch)
        for to_index in self.to_index:
            self.add_into_index(to_index, self.name, self.uri, self.branch)

if __name__ == "__main__":
    from repoxplorer.index import projects
    prjs = projects.Projects()
    for prj in prjs.get_projects():
        p = ProjectIndexer(prj['name'],
                           prj['uri'],
                           prj['branch'])
        p.git_init()
        p.git_fetch_branch()
        p.git_get_commit_obj()
        p.get_current_commit_indexed()
        p.compute_to_index_to_delete()
        p.index()
