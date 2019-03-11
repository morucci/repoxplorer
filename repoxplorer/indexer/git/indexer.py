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
import sys
import copy
import shutil
import pickle
import logging
import subprocess
import multiprocessing as mp

from pecan import conf

from repoxplorer import index
from repoxplorer.index.tags import Tags
from repoxplorer.index.commits import Commits
from repoxplorer.index.tags import PROPERTIES as T_PROPERTIES
from repoxplorer.index.commits import PROPERTIES as C_PROPERTIES
from repoxplorer.indexer.git import metadata_re

logger = logging.getLogger(__name__)

AUTHOR_RE = re.compile('author (.*) <(.*)> (.*) (.*)')
COMMITTER_RE = re.compile('committer (.*) <(.*)> (.*) (.*)')
STATSL_RE = re.compile('(.*)\t(.*)\t(.*)')
FILE_RENAME_RE = re.compile(r"(.*){(.*)\s=>\s(.*)}(.*)")

EL_RESERVED_FIELDS = [
    '_index',
    '_uid',
    '_type',
    '_id',
    '_source',
    '_size',
    '_all',
    '_field_names',
    '_timestamp',
    '_ttl',
    '_parent',
    '_routing',
    '_meta',
]

RESERVED_METADATA_KEYS = (
    list(C_PROPERTIES.keys()) +
    list(T_PROPERTIES.keys()) +
    EL_RESERVED_FIELDS
)

SEEN_REFS_CACHED = 'seen-refs.cached'


def run(cmd, path):
    process = subprocess.Popen(cmd,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               cwd=path)
    out, err = process.communicate()
    if process.returncode != 0:
        logger.debug(err)
        raise Exception('%s exited with code %s' % (cmd, process.returncode))
    return out.decode()


def parse_commit_line(line, re, key=None):
    m = re.match(line)
    if m:
        if key:
            value = m.groups()[0]
            return key, value.strip().replace('#', '')
        key = m.groups()[0]
        if key not in RESERVED_METADATA_KEYS:
            value = m.groups()[1]
            # Remove space before and after the string and remove
            # the \# that will cause trouble when metadata are queried
            # via the URL arguments
            return key.strip(), value.strip().replace('#', '')


def parse_commit_msg(msg, extra_parsers=None):
    metadatas = []
    lines = msg.split('\n')
    subject = lines[0]
    for line in lines[1:]:
        for key, parser in metadata_re.METADATA_REs.items():
            metadata = parse_commit_line(line, parser, key=key)
            if metadata:
                metadatas.append(metadata)
        if not extra_parsers:
            continue
        for parser in extra_parsers:
            metadata = parse_commit_line(line, parser)
            if metadata:
                metadatas.append(metadata)
    return subject, metadatas


def get_all_shas(path):
    out = run(['git', 'log', '--format=format:%H', 'FETCH_HEAD'], path)
    shas = out.splitlines()
    return shas


def get_commits_desc(path, shas):
    if not shas:
        # Return an empty buf if not sha given
        # We do not whant git show return stat
        # of the tip of the branch
        return []
    cmd = ['git', 'show', '--format=raw', '--numstat']
    cmd.extend(shas)
    out = run(cmd, path)
    return out.splitlines()


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
        cmt['%s_name' % field] = m.groups()[0]
        cmt['%s_email' % field] = m.groups()[1]
        cmt['%s_email_domain' % field] = m.groups()[1].split('@')[-1]
        cmt['%s_date' % field] = int(m.groups()[2])
        cmt['%s_date_tz' % field] = m.groups()[3]
    cmt['ttl'] = cmt['committer_date'] - cmt['author_date']
    # Avoid weird negative TTL (personal computers may not be sync on NTP)
    cmt['ttl'] = cmt['ttl'] if cmt['ttl'] >= 0 else 0
    cmt['line_modifieds'] = 0
    cmt['files_stats'] = {}
    cmt['files_list'] = []
    cmt['commit_msg'] = ""
    cmt['commit_msg_full'] = ""
    cmt['signed'] = False
    try:
        input[offset + 2]
    except IndexError:
        return cmt, offset
    if input[offset + 2] == 'gpgsig -----BEGIN PGP SIGNATURE-----':
        cmt['signed'] = True
        offset += 3
        i = 0
        while True:
            if input[offset + i] == ' -----END PGP SIGNATURE-----':
                break
            i += 1
        offset += i + 1
    else:
        offset += 2
    while len(input[offset]):
        # Consuming the rest of headers until the empty line
        offset += 1
    offset += 1
    # Now we start to consume the commit message
    i = 0
    while True:
        try:
            input[offset + i]
        except IndexError:
            break
        if len(input[offset + i]):
            # Commit msg lines starts with a space char but I seen
            # exceptions so check if a stat or commit line match
            m = STATSL_RE.match(input[offset + i])
            if m or input[offset + i].startswith('commit'):
                break
        i += 1
    cmt['commit_msg_full'] = "\n".join(
        [l.strip() for l in input[offset:offset+i]])
    subject, metadatas = parse_commit_msg(
        cmt['commit_msg_full'], extra_parsers)
    cmt['commit_msg'] = subject
    for metadata in metadatas:
        if metadata[0] not in cmt:
            cmt[metadata[0]] = []
        cmt[metadata[0]].append(metadata[1])
    offset += i
    # Now we start to consume the stats fields
    i = 0
    cmt['files_list'] = set()
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
            m = STATSL_RE.match(input[offset + i])
            if m.groups()[0] != '-':
                # '-' means binary file - so skip it
                l_added = int(m.groups()[0])
                l_removed = int(m.groups()[1])
                file = m.groups()[2]
                file = FILE_RENAME_RE.sub(r'\1\3\4', file)
                cmt['files_list'].add(file)
                pe = file.split('/')
                for pei in range(1, len(pe)+1):
                    cmt['files_list'].add('/'.join(pe[0:pei]))
                cmt['files_stats'][file] = {
                    'lines_added': l_added,
                    'lines_removed': l_removed}
                cmt['line_modifieds'] += l_added + l_removed
        i += 1
    cmt['files_list'] = sorted(list(cmt['files_list']))
    return cmt, offset + i


def process_commits_desc_output(input, ref_ids, extra_parsers=None):
    ret = []
    offset = 0
    while True:
        try:
            input[offset]
        except IndexError:
            break
        try:
            cmt, offset = parse_commit(input, offset, extra_parsers)
            cmt['repos'] = ref_ids
            # Remove atm un-supported fields
            for f in ("author_date_tz", "committer_date_tz",
                      "committer_email_domain", "files_stats",
                      "signed", "commit_msg_full"):
                del cmt[f]
            ret.append(cmt)
        except Exception as e:
            logger.warning("A chunk of commits failed to be parsed. Skip.")
            logger.warning("Skip it !")
            logger.debug("Output of the failed chunk at the offset %s" % (
                offset))
            logger.debug("\n".join(input[offset:offset+100]))
            logger.exception("Issue was: %s" % e)
            break
    return ret


def process_commits(options):
    path, ref_ids, shas = options
    if not isinstance(ref_ids, list):
        ref_ids = [ref_ids]
    c = Commits(index.Connector())
    logger.info("Worker %s started to extract and index %s commits" % (
        mp.current_process(), len(shas)))
    buf = get_commits_desc(path, shas)
    c.add_commits(process_commits_desc_output(buf, ref_ids))


def delete_commits(commits, name, to_delete, ref_id):
    res = commits.get_commits_by_id(list(to_delete))
    docs = [c['_source'] for
            c in res['docs'] if c['found'] is True]
    # If it remains the meta_ref + ref (to delete) we can process
    # with the deletion
    to_delete = [
        c['sha'] for c in docs if (
            len(c['repos']) == 1 or
            (len(c['repos']) == 2 and
             [x for x in c['repos'] if x.startswith('meta_ref: ')]
             )
        )
    ]
    to_delete_update = [
        c['sha'] for c in docs if (
            (len(c['repos']) > 1 and not
             [x for x in c['repos'] if x.startswith('meta_ref: ')]
             ) or
            (len(c['repos']) > 2 and
             [x for x in c['repos'] if x.startswith('meta_ref: ')]
             )
         )
    ]

    if to_delete:
        logger.info("%s: %s commits will be deleted ..." % (
            name, len(to_delete)))
        commits.del_commits(to_delete)

    if to_delete_update:
        logger.info("%s: %s commits belonging to other repos "
                    "will be updated ..." % (
                        name, len(to_delete_update)))
        res = commits.get_commits_by_id(to_delete_update)
        if res:
            original_commits = [c['_source'] for
                                c in res['docs']]
            for c in original_commits:
                c['repos'].remove(ref_id)
            commits.update_commits(original_commits)


class RefsCleaner():
    def __init__(self, projects, con=None):
        if not con:
            self.con = index.Connector()
        else:
            self.con = con
        self.projects = projects
        self.c = Commits(self.con)
        self.t = Tags(index.Connector(
            index=self.con.index, index_suffix='tags'))
        self.seen_refs_path = os.path.join(conf.db_path, SEEN_REFS_CACHED)
        self.current_base_ids = set()

    def find_refs_to_clean(self):
        projects = self.projects.get_projects(source=['refs'])
        refs_ids = set()
        for project in projects.values():
            for ref in project['refs']:
                self.current_base_ids.add(ref['shortrid'])
                refs_ids.add(ref['fullrid'])
        if not os.path.isfile(self.seen_refs_path):
            self.data = set()
        else:
            try:
                self.data = pickle.load(open(self.seen_refs_path, 'rb'))
            except Exception:
                # Protect against corrupted file
                self.data = set()
        refs_to_clean = self.data - refs_ids
        if len(refs_to_clean):
            logger.info("Found %s refs to clean." % len(refs_to_clean))
        return refs_to_clean

    def clean_tags(self, base_id):
        # Tags are indexed by repos (base_id) not by ref (ref_id)
        tags = self.t.get_tags([base_id])
        ids = [t['_id'] for t in tags]
        if ids:
            logger.info("Repo %s no longer referenced. Cleaning %s tags" % (
                base_id, len(ids)))
            self.t.del_tags(ids)

    def clean_ref_cmts(self, ref):
        # Find ref's Commits
        ids = [c['_id'] for c in
               self.c.get_commits(repos=[ref], scan=True)]
        if not ids:
            self.remove_from_seen_refs(ref)
            return
        logger.info("Ref %s no longer referenced. Cleaning %s cmts." %
                    (ref, len(ids)))
        # Do it by bulk of 10000 to not hurt memory
        bulk = 10000
        i = 0
        while True:
            _ids = ids[i:i+bulk]
            if not _ids:
                break
            else:
                delete_commits(self.c, ref, _ids, ref)
                i += bulk

    def clean(self, refs):
        base_ids = set()
        for ref in refs:
            self.clean_ref_cmts(ref)
            self.remove_from_seen_refs(ref)
            base_id = ref.replace(":%s" % ref.split(':')[-1], "")
            if base_id not in self.current_base_ids:
                base_ids.add(base_id)
        for base_id in base_ids:
            self.clean_tags(base_id)

    def remove_from_seen_refs(self, ref_id):
        # Remove from the struct to be dumped
        self.data.remove(ref_id)
        pickle.dump(self.data, open(self.seen_refs_path, 'wb'))


class RepoIndexer():
    def __init__(self, name, uri, parsers=None,
                 con=None, meta_ref=None):
        if not con:
            self.con = index.Connector()
        else:
            self.con = con
        self.c = Commits(self.con)
        self.t = Tags(index.Connector(
            index=self.con.index, index_suffix='tags'))
        if not os.path.isdir(conf.git_store):
            os.makedirs(conf.git_store)
        self.name = name
        self.uri = uri
        self.base_id = '%s:%s' % (self.uri, self.name)
        self.seen_refs_path = os.path.join(conf.db_path, SEEN_REFS_CACHED)
        if meta_ref:
            self.meta_ref = 'meta_ref: %s' % meta_ref
        else:
            self.meta_ref = None

        if not parsers:
            self.parsers = []
        else:
            self.parsers = parsers
        self.parsers_compiled = False
        self.local = os.path.join(conf.git_store,
                                  self.name,
                                  self.uri.replace('/', '_'))
        if not os.path.isdir(self.local):
            os.makedirs(self.local)

        self.credentials_helper_path = getattr(
            conf, 'git_credential_helper_path', None)
        if not (self.credentials_helper_path and
                self.credentials_helper_path.startswith('/') and
                os.path.isfile(self.credentials_helper_path)):
            logger.warning('Configured git_credential_helper not found')
            self.credentials_helper_path = None
        # Look at the default installation pathes
        if not self.credentials_helper_path:
            self.credentials_helper_path = os.path.join(
                sys.prefix, 'bin', 'repoxplorer-git-credentials-helper')
            if not os.path.isfile(self.credentials_helper_path):
                self.credentials_helper_path = shutil.which(
                    'repoxplorer-git-credentials-helper')
            if not self.credentials_helper_path:
                logger.warning(
                    'Default repoxplorer-git-credential-helper command '
                    'not found')

    def __str__(self):
        return 'Git indexer of %s' % self.ref_id

    def save_seen_ref_in_cache(self):
        # Keep a cache a each ref that have been indexed
        # This is use later to discover seen refs no longer in projects.yaml
        # In that case a removal from the backend will be performed
        logger.debug("Save ref %s into seen_refs file" % self.ref_id)
        if not os.path.isfile(self.seen_refs_path):
            data = set()
        else:
            try:
                data = pickle.load(open(self.seen_refs_path, 'rb'))
            except Exception:
                # Protect against corrupted file
                data = set()
        data.add(self.ref_id)
        pickle.dump(data, open(self.seen_refs_path, 'wb'))

    def set_branch(self, branch):
        self.branch = branch
        self.ref_id = '%s:%s:%s' % (self.uri, self.name, self.branch)
        self.save_seen_ref_in_cache()

    def git_init(self):
        logger.debug("Git init for %s:%s in %s" % (
            self.uri, self.name, self.local))
        run(["git", "init", "--bare", "."], self.local)
        remotes = run(["git", "remote", "-v"], self.local)
        remote_names = [line.split()[0] for line in remotes.splitlines()]
        if "origin" not in remote_names:
            run(["git", "remote", "add", "origin", self.uri], self.local

    def git_fetch_branch(self):
        logger.debug("Fetch %s %s:%s" % (self.name, self.uri,
                                         self.branch))
        run(["git", "-c",
             "credential.helper=%s" % self.credentials_helper_path,
             "fetch", "-nk", "origin", "+%s:%s" % (self.branch, self.branch)],
            self.local)

    def get_refs(self):
        refs = run([
            "git", "-c", "credential.helper=%s" % self.credentials_helper_path,
            "ls-remote", "origin"], self.local).splitlines()
        self.refs = []
        for r in refs:
            self.refs.append(r.split('\t'))

    def get_heads(self):
        self.heads = [x for x in self.refs if x[1].startswith('refs/heads/')]

    def get_tags(self):
        self.tags = [x for x in self.refs if x[1].startswith('refs/tags/')]

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
        ref_ids = [self.ref_id]
        if self.meta_ref:
            ref_ids.append(self.meta_ref)
        options = [
            (self.local, ref_ids, stp) for stp in to_process]
        worker_pool = mp.Pool(workers)
        worker_pool.map(process_commits, options)
        worker_pool.terminate()
        worker_pool.join()

    def is_branch_fully_indexed(self):
        branch = [head for head in self.heads if
                  head[1].endswith(self.branch)][0]
        branch_tip_sha = branch[0]
        cmt = self.c.get_commit(branch_tip_sha, silent=True)
        if cmt and self.ref_id in cmt['repos']:
            return True
        return False

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

    def compute_to_create_to_update(self):
        if self.to_index:
            res = self.c.get_commits_by_id(list(self.to_index))
            to_update = [c['_source'] for
                         c in res['docs'] if c['found'] is True]
            to_create = [c['_id'] for
                         c in res['docs'] if c['found'] is False]
            return to_create, to_update
        return [], []

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
            if not self.parsers_compiled:
                raw_parsers = copy.deepcopy(self.parsers)
                self.parsers = []
                for parser in raw_parsers:
                    self.parsers.append(re.compile(parser))
                logger.debug(
                    "%s: Prepared %s regex parsers for commit msgs" % (
                        self.name, len(self.parsers)))
                self.parsers_compiled = True

        # check whether a commit should be completly deleted or
        # updated by removing the repo from the repos field
        if self.to_delete:
            delete_commits(self.c, self.name, self.to_delete, self.ref_id)

        # check whether a commit should be created or
        # updated by adding the repo into the repos field
        if self.to_index:
            to_create, to_update = self.compute_to_create_to_update()

            if to_create:
                logger.info("%s: %s commits will be created ..." % (
                    self.name, len(to_create)))
                self.run_workers(to_create, extract_workers)

            if to_update:
                logger.info(
                    "%s: %s commits already indexed and need to be updated" % (
                        self.name, len(to_update)))
                for c in to_update:
                    c['repos'].append(self.ref_id)
                self.c.update_commits(to_update)
