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
import yaml
import github3
import argparse
import requests

# This is a small tool to read the RDO rdoinfo file
# and create a repoXplorer compatible projects.yaml file.

INFO_URI = (
        "https://raw.githubusercontent.com/"
        "RedHatOfficial/RedHatOfficial.github.io/"
        "dev/app/data/projects.json")

parser = argparse.ArgumentParser(
    description='Read/Index RedhatOffical projects file')
parser.add_argument(
    '--output-path', type=str,
    help='yaml file path to register organization repositories details')

args = parser.parse_args()


def fetch_repos(org, template, repo=None):
    anon = github3.GitHub(
        'morucci2', token='')
    org = anon.organization(org)
    data = {}
    if not org:
        print(
            "Org %s not found, try to find single"
            " user's repos ..." % org)
        repos = anon.repositories_by(org)
    else:
        repos = org.repositories()
    for r in repos:
        if repo and r.name != repo:
            continue
        if r.fork:
            continue
        data[r.name] = {
            "branches": [r.default_branch],
        }
        data[r.name]["template"] = template
    return data


if __name__ == "__main__":
    gp = yaml.safe_load(requests.get(INFO_URI).text)

    projects = {}
    templates = {}
    struct = {'projects': projects,
              'project-templates': templates}

    c = len(gp)
    for project in gp:
        print project
        print "Remain: %d" % c
        c -= 1
        uri = project['projectRepository'].rstrip('/')
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

        projects[project['projectName']] = {
            'repos': fetch_repos(org, project['projectName'], repo),
            'description': project['projectDescription'],
        }
        templates[project['projectName']] = {
            "branches": ["master"],
            "uri": orguri + "/%(name)s",
            "gitweb": orguri + "/%(name)s/commit/%%(sha)s",
            "tags": [project['category']]
        }

    path = 'redhatoffical.yaml'
    if args.output_path:
        path = os.path.join(os.path.expanduser(args.output_path), path)

    with open(path, 'w') as fd:
        fd.write(yaml.safe_dump(struct,
                                default_flow_style=False))
    print
    print ("RedHatOffical source repositories details"
           " has been written to %s" % path)

    print ("Please edit the yaml file if needed (like adding additional"
           " branches to index, defines custom releases, ...)")

    sys.exit(0)
