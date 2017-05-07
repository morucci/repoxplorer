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


def run(cmd, path):
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               cwd=path)
    out, err = process.communicate()
    if process.returncode != 0:
        raise Exception('%s exited with code %s' % (cmd, process.returncode))
    return out


def get_shas(path):
    out = run(['git', 'log', '--format=format:%H'], path)
    shas = out.splitlines()
    return shas


def get_commits_desc(path, to_sha='HEAD', from_sha=''):
    if from_sha:
        from_sha = '%s..' % from_sha
    out = run(['git', 'log', '--format=raw', '--numstat',
               '%s%s' % (from_sha, to_sha), '.'],
              path=path)
    return out.splitlines()


def parse_commit(input, offset):
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
    offset += 3
    i = 0
    cmt['commit_msg'] = input[offset].strip()
    while True:
        if len(input[offset + i]) and input[offset + i][0] != ' ':
            # Commit msg lines starts with a space char
            break
        i += 1
    cmt['commit_msg_full'] = "\n".join(
        [l.strip() for l in input[offset:offset+i]])
    if cmt['merge_commit']:
        return cmt, offset + i
    offset += i + 1
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
        if len(input[offset + i]) and input[offset + i][0] != ' ':
            m = re.match("(.*)\t(.*)\t(.*)", input[offset + i])
            if not m:
                print input[offset + i]
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


def process_commits_desc_output(input):
    ret = []
    offset = 0
    while True:
        try:
            input[offset]
        except IndexError:
            break
        cmt, offset = parse_commit(input, offset)
        ret.append(cmt)
    return ret


if __name__ == "__main__":
    if len(sys.argv) > 1:
        path = sys.argv[1]
        shas = get_shas(path)
        buf = get_commits_desc(path)
    else:
        path = '/home/fabien/git/softwarefactory-project.io-git/repoxplorer/'
        buf = file(
            os.path.dirname(
                os.path.abspath(__file__)) + '/text.out').read().splitlines()
    cmts = process_commits_desc_output(buf)
    print len(cmts)
    print cmts[0]
    print cmts[-1]
    print "end of test"
