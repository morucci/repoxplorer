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
import subprocess
import multiprocessing as mp

from repoxplorer.index.commits import PROPERTIES

METADATA_RE = re.compile('^([a-zA-Z-0-9_-]+):([^//].+)$')


def run(cmd, path):
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               cwd=path)
    out, err = process.communicate()
    if process.returncode != 0:
        raise Exception('%s exited with code %s' % (cmd, process.returncode))
    return out


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


def get_all_shas(path):
    out = run(['git', 'log', '--format=format:%H'], path)
    shas = out.splitlines()
    return shas


def get_commits_desc(path, shas):
    cmd = ['git', 'show', '--format=raw', '--numstat']
    cmd.extend(shas)
    out = run(cmd, path=path)
    return out.splitlines()


def parse_commit(input, offset, extra_parsers=None):
    cmt = {}
    cmt['sha'] = input[offset].split()[-1]
    # input[2] is the parent hash and if input[3] refers
    # also to a parent hash then this is a merge commit
    if input[offset + 3].startswith('parent'):
        cmt['merge_commit'] = True
        offset += 4
    elif input[offset + 3].startswith('committer'):
        # First commit of the chain - no parent
        cmt['merge_commit'] = False
        offset += 2
    else:
        cmt['merge_commit'] = False
        offset += 3
    for i, field in ((0, "author"), (1, "committer")):
        m = re.match("%s (.*) <(.*)> (.*) (.*)" % field,
                     input[offset+i])
        cmt['%s_name' % field] = m.groups()[0]
        cmt['%s_email' % field] = m.groups()[1]
        cmt['%s_email_domain' % field] = m.groups()[1].split('@')[-1]
        cmt['%s_date' % field] = int(m.groups()[2])
        cmt['%s_date_tz' % field] = m.groups()[3]
    cmt['ttl'] = cmt['committer_date'] - cmt['author_date']
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
        if len(input[offset + i]) and input[offset + i][0] != ' ':
            # Commit msg lines starts with a space char
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
    # if cmt['merge_commit']:
    #    return cmt, offset + i
    # offset += i + 1
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


def process_commits_desc_output(input, extra_parsers=None):
    ret = []
    offset = 0
    while True:
        try:
            input[offset]
        except IndexError:
            break
        cmt, offset = parse_commit(input, offset, extra_parsers)
        ret.append(cmt)
    return ret


def process_commits(options):
    path, shas = options
    print "Worker %s started to extract %s commits" % (
        mp.current_process(), len(shas))
    buf = get_commits_desc(path, shas)
    cmts = process_commits_desc_output(buf)
    return cmts


def run_workers(path, shas, workers=1):
    BULK_CHUNK = 1000
    to_process = []
    while True:
        try:
            shas[BULK_CHUNK]
            to_process.append(shas[:BULK_CHUNK])
            del shas[:BULK_CHUNK]
        except IndexError:
            # Add the rest
            to_process.append(shas)
            break
    options = [(path, stp) for stp in to_process]
    worker_pool = mp.Pool(workers)
    extracted = worker_pool.map(process_commits, options)
    worker_pool.terminate()
    worker_pool.join()
    ret = []
    for r in extracted:
        ret.extend(r)
    return ret


if __name__ == "__main__":
    path = sys.argv[1]
    shas = get_all_shas(path)
    cmts = run_workers(path, shas, workers=4)
    # cmts = process_commits((path, shas[:5]))
    print len(cmts)
    print cmts[0]
    print cmts[-1]
