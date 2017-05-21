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
import subprocess
import multiprocessing as mp

from pecan import conf
from pecan import configuration

from repoxplorer import index
from repoxplorer.index.tags import Tags
from repoxplorer.index.commits import Commits
from repoxplorer.index.commits import PROPERTIES

logger = logging.getLogger(__name__)

METADATA_RE = re.compile('^([a-zA-Z-0-9_-]+):([^//].+)$')
AUTHOR_RE = re.compile('author (.*) <(.*)> (.*) (.*)')
COMMITTER_RE = re.compile('committer (.*) <(.*)> (.*) (.*)')


def run(cmd, path):
    process = subprocess.Popen(cmd,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               cwd=path)
    out, err = process.communicate()
    if process.returncode != 0:
        logger.debug(err)
        raise Exception('%s exited with code %s' % (cmd, process.returncode))
    return out


def parse_commit_line(line, re):
    reserved_metadata_keys = PROPERTIES.keys()
    m = re.match(line)
    if m:
        key = m.groups()[0]
        if key not in reserved_metadata_keys:
            value = m.groups()[1]
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
    subject = lines[0]
    for line in lines[1:]:
        for parser in parsers:
            metadata = parse_commit_line(line, parser)
            if metadata:
                metadatas.append(metadata)
    return subject, metadatas


def get_all_shas(path):
    out = run(['git', 'log', '--format=format:%H'], path)
    shas = out.splitlines()
    return shas


def get_commits_desc(path, shas):
    cmd = ['git', 'show', '--format=raw', '--numstat']
    cmd.extend(shas)
    out = run(cmd, path)
    return out.splitlines()


def _decode(s):
    return s.decode('utf-8', errors="replace")


def parse_commit(input, offset, extra_parsers=None):
    cmt = {}
    cmt['sha'] = input[offset].split()[-1]
    # input[offset + 1] is the tree hash
    # input[offset + 2] is the parent hash
    offset += 2
    parents = 0
    if not input[offset].startswith('parent'):
        # No parent so first commit of the chain
        pass
    else:
        while True:
            if input[offset].startswith('parent'):
                offset += 1
                parents += 1
            else:
                break
    if parents > 1:
        cmt['merge_commit'] = True
    else:
        cmt['merge_commit'] = False
    for i, r, field in ((0, AUTHOR_RE, 'author'),
                        (1, COMMITTER_RE, 'committer')):
        m = re.match(r, input[offset+i])
        cmt['%s_name' % field] = _decode(m.groups()[0])
        cmt['%s_email' % field] = _decode(m.groups()[1])
        cmt['%s_email_domain' % field] = _decode(m.groups()[1].split('@')[-1])
        cmt['%s_date' % field] = int(m.groups()[2])
        cmt['%s_date_tz' % field] = m.groups()[3]
    cmt['ttl'] = cmt['committer_date'] - cmt['author_date']
    # Avoid weird negative TTL (personal computers may not be sync on NTP)
    cmt['ttl'] = cmt['ttl'] if cmt['ttl'] >= 0 else 0
    if input[offset + 2] == 'gpgsig -----BEGIN PGP SIGNATURE-----':
        cmt['signed'] = True
        offset += 3
        i = 0
        while True:
            if input[offset + i] == ' -----END PGP SIGNATURE-----':
                break
            i += 1
        offset += i + 2
    else:
        cmt['signed'] = False
        offset += 3
    i = 0
    while True:
        try:
            input[offset + i]
        except IndexError:
            break
        if len(input[offset + i]) and input[offset + i][0] != ' ':
            # Commit msg lines starts with a space char
            break
        i += 1
    cmt['commit_msg_full'] = _decode("\n".join(
        [l.strip() for l in input[offset:offset+i]]))
    subject, metadatas = parse_commit_msg(
        cmt['commit_msg_full'], extra_parsers)
    cmt['commit_msg'] = subject
    for metadata in metadatas:
        if metadata[0] not in cmt:
            cmt[metadata[0]] = []
        cmt[metadata[0]].append(metadata[1])
    offset += i
    i = 0
    cmt['line_modifieds'] = 0
    cmt['files_stats'] = {}
    while True:
        try:
            input[offset + i]
        except IndexError:
            # EOF
            break
        if input[offset + i].startswith('commit'):
            # Next commit
            break
        if (len(input[offset + i]) and input[offset + i][0] != ' ' and not
                cmt['merge_commit']):
            m = re.match("(.*)\t(.*)\t(.*)", input[offset + i])
            if m.groups()[0] != '-':
                # '-' means binary file - so skip it
                l_added = int(m.groups()[0])
                l_removed = int(m.groups()[1])
                file = m.groups()[2]
                cmt['files_stats'][file] = {
                    'lines_added': l_added,
                    'lines_removed': l_removed}
                cmt['line_modifieds'] += l_added + l_removed
        i += 1
    return cmt, offset + i


def process_commits_desc_output(input, ref_id, extra_parsers=None):
    ret = []
    offset = 0
    while True:
        try:
            input[offset]
        except IndexError:
            break
        try:
            cmt, offset = parse_commit(input, offset, extra_parsers)
        except Exception:
            logger.warning("A chunk of commits failed to be parsed. Skip.")
            logger.warning("Skip it !")
            logger.debug("Output of the failed chunk at the offset %s" % (
                offset))
            logger.debug("\n".join(input[offset:offset+100]))
            logger.exception("Issue was:")
        cmt['repos'] = [ref_id, ]
        # Remove atm un-supported fields
        del cmt["author_date_tz"]
        del cmt["committer_date_tz"]
        del cmt["author_email_domain"]
        del cmt["committer_email_domain"]
        del cmt["files_stats"]
        del cmt["signed"]
        del cmt["commit_msg_full"]
        ret.append(cmt)
    return ret


def process_commits(options):
    path, ref_id, shas = options
    logger.info("Worker %s started to extract %s commits" % (
        mp.current_process(), len(shas)))
    buf = get_commits_desc(path, shas)
    cmts = process_commits_desc_output(buf, ref_id)
    return cmts


class RepoIndexer():
    def __init__(self, name, uri, parsers=None,
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
        self.base_id = '%s:%s' % (self.uri, self.name)
        if not parsers:
            self.parsers = []
        else:
            self.parsers = parsers
        self.local = os.path.join(conf.git_store,
                                  self.name,
                                  self.uri.replace('/', '_'))
        if not os.path.isdir(self.local):
            os.makedirs(self.local)

    def __str__(self):
        return 'Git indexer of %s' % self.ref_id

    def set_branch(self, branch):
        self.branch = branch
        self.ref_id = '%s:%s:%s' % (self.uri, self.name, self.branch)

    def git_init(self):
        logger.debug("Git init for %s:%s in %s" % (
            self.uri, self.name, self.local))
        run(["git", "init", "."], self.local)
        if "origin" not in run(["git", "remote", "-v"], self.local):
            run(["git", "remote", "add", "origin", self.uri], self.local)

    def git_fetch_branch(self):
        logger.debug("Fetch %s %s:%s" % (self.name, self.uri,
                                         self.branch))
        run(["git", "fetch", "origin", self.branch], self.local)
        run(["git", "checkout", "FETCH_HEAD"], self.local)

    def get_refs(self):
        refs = run(["git", "ls-remote",
                   "origin"], self.local).splitlines()
        self.refs = []
        for r in refs:
            self.refs.append(r.split('\t'))

    def get_heads(self):
        self.heads = filter(
            lambda x: x[1].startswith('refs/heads/'), self.refs)

    def get_tags(self):
        self.tags = filter(
            lambda x: x[1].startswith('refs/tags/'), self.refs)

    def git_get_commit_obj(self):
        self.commits = get_all_shas(self.local)

    def run_workers(self, shas, workers):
        BULK_CHUNK = 1000
        to_process = []
        if workers == 0:
            # Default value (auto)
            workers = mp.cpu_count() - 1 or 1
        while True:
            try:
                shas[BULK_CHUNK]
                to_process.append(shas[:BULK_CHUNK])
                del shas[:BULK_CHUNK]
            except IndexError:
                # Add the rest
                to_process.append(shas)
                break
        options = [(self.local, self.ref_id, stp) for stp in to_process]
        worker_pool = mp.Pool(workers)
        extracted = worker_pool.map(process_commits, options)
        worker_pool.terminate()
        worker_pool.join()
        ret = []
        for r in extracted:
            ret.extend(r)
        return ret

    def get_current_commit_indexed(self):
        """ Fetch from the index commits mentionned for this repo
        and branch.
        """
        self.already_indexed = [c['_id'] for c in
                                self.c.get_commits(repos=[self.ref_id],
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
        tags = self.t.get_tags([self.base_id])
        existing = dict([(c_tid(t['_source']), t['_id']) for t in tags])
        logger.debug('%s: %s tags already referenced' % (
                     self.name, len(existing)))
        # Some commits may be not found because it is possible the branches
        # has not been indexed.
        commits = [c['_source'] for c in self.c.get_commits_by_id(
                   [t[0] for t in self.tags])['docs'] if c['found']]
        lookup = dict([(c['sha'], c['committer_date']) for c in commits])
        to_delete = [v for k, v in existing.items() if
                     k not in ["%s%s%s" % (sha,
                                           name.replace('refs/tags/',
                                                        '').replace('^{}', ''),
                                           self.base_id) for
                               sha, name in self.tags]]
        docs = []
        for sha, name in self.tags:
            if sha in lookup:
                doc = {}
                doc['name'] = name.replace('refs/tags/', '').replace('^{}', '')
                doc['sha'] = sha
                doc['date'] = lookup[sha]
                doc['repo'] = self.base_id
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
                    c['repos'].remove(self.ref_id)
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
            # Here we use sub processes workers to speedup
            # getting commits stats
            self.c.add_commits(
                self.run_workers(to_create, extract_workers))

            logger.info(
                "%s: %s commits already indexed and need to be updated" % (
                    self.name, len(to_update)))
            for c in to_update:
                c['repos'].append(self.ref_id)
            self.c.update_commits(to_update)
