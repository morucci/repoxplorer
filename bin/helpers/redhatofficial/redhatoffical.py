#!/usr/bin/env python

# Copyright 2018, Red Hat
# Copyright 2018, Fabien Boucher
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

import os
import sys
import json
import yaml
import github3
import argparse
import requests

# This is a small tool to read the redhatofficial project file
# and create a repoXplorer compatible projects.yaml files.

# Configuration file syntax
# # GH API key needed to reduce rate limit issues
# gh_api_key: ABC


class NoRepoException(Exception):
    pass


INFO_URI = (
        "https://raw.githubusercontent.com/"
        "RedHatOfficial/RedHatOfficial.github.io/"
        "dev/app/data/projects.json")

parser = argparse.ArgumentParser(
    description='Read/Index RedhatOffical projects file')
parser.add_argument(
    '--output-path', type=str,
    help='yaml file path to register organization repositories details')
parser.add_argument(
    '--config-path', type=str, default='rho-gh.yaml',
    help='path to the yaml configuration')

args = parser.parse_args()


def fetch_repos(gh_api_key, org, template, repo=None, query=None):
    gh = github3.GitHub('', token=gh_api_key)
    orga = gh.organization(org)
    data = {}
    if not orga:
        print(
            "Org %s not found, try to find single"
            " user's repos ..." % org)
        repos = gh.repositories_by(org)
    else:
        repos = orga.repositories()
    for r in repos:
        if repo and r.name != repo:
            continue
        if r.fork:
            continue
        if query and query not in r.name:
            continue
        data[r.name] = {
            "branches": [r.default_branch],
        }
        data[r.name]["template"] = template
    if not data:
        raise NoRepoException()
    return data


if __name__ == "__main__":
    if not os.path.isfile(args.config_path):
        print("Unable to find %s" % args.config_path)
    try:
        with open(args.config_path) as cf:
            conf = yaml.load(cf.read())
    except Exception as e:
        print("Unable to read %s" % args.config_path)
        print e
        sys.exit(-1)

    gp = json.loads(requests.get(INFO_URI).text)

    c = len(gp)
    for project in gp:
        projects = {}
        templates = {}
        struct = {'projects': projects,
                  'project-templates': templates}
        print(project)
        print("Remain: %d" % c)
        c -= 1
        uri = project['projectRepository'].rstrip('/')
        if '?q=' in uri:
            query = uri.split('?q=')[1]
            uri = uri.split('?q=')[0]
            print("There is a query on %s for %s" % (uri, query))
        else:
            query = None
        uris = uri.split('/')
        if uris[-2] == 'github.com':
            # It is a github org
            org = uris[-1]
            repo = None
            orguri = uri
        else:
            # It is a single github repo
            org = uris[-2]
            repo = uris[-1]
            orguri = "/".join(uris[0:-1])

        try:
            projects[project['projectName']] = {
                'repos': fetch_repos(conf.get('gh_api_key', ''), org,
                                     project['projectName'], repo, query),
                'description': project['projectDescription'],
            }
        except NoRepoException:
            print('No repository for the project %s. Skip' % (
                project['projectName']))
            continue
        templates[project['projectName']] = {
            "branches": ["master"],
            "uri": orguri + "/%(name)s",
            "gitweb": orguri + "/%(name)s/commit/%%(sha)s",
        }

        path = '%s.yaml' % project['projectName'].replace('/', '-')
        if args.output_path:
            path = os.path.join(os.path.expanduser(args.output_path), path)

        with open(path, 'w') as fd:
            fd.write(yaml.safe_dump(struct,
                                    default_flow_style=False))

        print("Source repositories details has been written to %s" % path)

    sys.exit(0)
