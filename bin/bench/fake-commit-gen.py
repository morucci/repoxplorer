#!/usr/bin/python

# Copyright 2016, Fabien Boucher
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import string
import random
import hashlib

from repoxplorer.index.commits import Commits
from repoxplorer import index

epoch_start = 1476633000


def create_random_str(lenght=6):
    value = "".join([random.choice(string.ascii_lowercase)
                    for _ in range(lenght)])
    return value


def gen_emails(amount):
    ret = []
    for i in range(amount):
        email = "%s@%s.%s" % (
            create_random_str(8),
            create_random_str(5),
            create_random_str(3),
        )
        name = "%s %s" % (
            create_random_str(8),
            create_random_str(8),
        )
        ret.append((name, email))
    return ret


def gen_commit_msg():
    return " ".join([create_random_str(random.randint(0, 10))
                     for _ in range(5)])


def gen_fake_commits(amount=10000):
    print("Start generation of %s fake commits" % amount)
    email_amount = amount * 0.03
    email_amount = int(email_amount)
    if not email_amount:
        email_amount = 1
    emails = gen_emails(email_amount)
    project = '%s:%s:%s' % (
        'https://github.com/openstack/test',
        'test', 'master')
    ret = []
    for i in range(amount):
        author_date = random.randint(
            epoch_start, epoch_start + 1000000)
        author = emails[random.randint(0, email_amount - 1)]
        committer = emails[random.randint(0, email_amount - 1)]
        c = {}
        c['sha'] = hashlib.sha256(create_random_str(10)).hexdigest()
        c['author_name'] = author[0]
        c['committer_name'] = committer[0]
        c['author_email'] = author[1]
        c['committer_email'] = committer[1]
        c['author_date'] = author_date
        c['committer_date'] = random.randint(
            author_date + 1, author_date + 10000)
        c['ttl'] = random.randint(0, 10000)
        c['commit_msg'] = gen_commit_msg()
        c['line_modifieds'] = random.randint(0, 10000)
        c['merge_commit'] = False
        c['projects'] = [project, ]
        ret.append(c)
    print("Generation of %s fake commits done." % amount)
    return ret


if __name__ == '__main__':
    amount = 100000
    c = Commits(index.Connector())
    c.add_commits(gen_fake_commits(amount))
    print("Indexation done.")
