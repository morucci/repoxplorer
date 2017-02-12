# RepoXplorer

RepoXplorer is a small stats and charts utility for Git repositories.
Its main purpose is to ease the visualization of stats for one or
more project(s) composed of multiple Git repositories.

As lot of projects are composed of multiple Git repositories (server,
client, libraries). RepoXplorer let's you describe how a project is composed
and then computes stats across them.

Furthermore it is possible to define author identities by listing
author emails and then avoid duplicated authors in the computed stats.

RepoXplorer relies on ElasticSearch. Only a Web browser is needed to access
the user interface.

## A visual overview of the user interface

![capture 1](https://raw.githubusercontent.com/morucci/repoxplorer/master/imgs/repoxplorer.jpg)

## How to install

First install repoXplorer in a virtualenv.

```Shell
virtualenv ~/repoxplorer
. ~/repoxplorer/bin/activate
pip install -r requirements.txt
python setup.py install
```

Install Elasticsearch. Here, we use an already "ready to use" Docker
container. But you should definitely use a regular installation
of ElasticSearch.

```Shell
~/repoxplorer/bin/el-start.sh
```

## How to index a list of Git hosted projects

A yaml file should be provisioned with the projects you want to index. The
file $prefix/local/share/repoxplorer/projects.yaml is expected to be found.

Below is the default projects.yaml file provided. Note that Barbican project
is composed of two Git repositories: the server and the client.

The branches key of a Git repository definition permits to defines which
branches to index. This key expects a list of branches name.

A list of tags can be given to each Git repositories. This tag notion
should not be considered as Git tags but only as a way to group
Git repositories together. For example tags like 'documentation', 'librairies',
...) could be considered.

A list of releases can be defined (can be also defined in a template).
It is useful when you want to define release points in a time accross
all repositories defined in a project. Release dates are added to detected
Git tags dates.

As of now RepoXplorer index and compute stats frim Git commit objects
and Git tags.

Edit this file to add projects you want to index.
~/repoxplorer/local/share/repoxplorer/projects.yaml.

```YAML
---
templates:
- name: default
  uri: https://github.com/openstack/%(name)s
  branches:
  - master
  - stable/mitaka
  - stable/newton
  gitweb: https://github.com/openstack/%(name)s/commit/%%(sha)s

projects:
  Barbican:
  - name: barbican
    tags:
      - python
    releases:
      - name: 2.0
        date: 20/12/2016
    template: default
  - name: python-barbicanclient
    tags:
      - python
    template: default
```

Then start the Git indexer manually.

```Shell
python ~/repoxplorer/bin/repoxplorer-indexer
```

In order to run the indexer continuously you can use the command
argument "--forever".

Furthermore you can install the systemd unit file for the indexer.

```
sudo cp etc/repoxplorer.service /usr/lib/systemd/system/repoxplorer.service
# Be sure to set the correct path to the repoxplorer-indexer script

sudo systemctl daemon-reload
sudo systemctl start repoxplorer
sudo systemctl status repoxplorer

# You can check the indexer log via journalctl
sudo journalctl -f
```

## Start the Web UI

Start the RepoXplorer web app.

```Shell
uwsgi --http-socket :8080 --pecan ~/repoxplorer/local/share/repoxplorer/config.py
```

Then open a Web browser to access http://localhost:8080. You will be faced to a list
of projects such as defined in projects.yaml. A click on one of the project's ids
will redirect you to the statistics page of the given project.

Furthermore you can install the systemd unit file for the webui.

```
sudo cp etc/repoxplorer-webui.service /usr/lib/systemd/system/repoxplorer-webui.service
# Be sure to set the correct path to the uwsgi tool and to the config.py file.

sudo systemctl daemon-reload
sudo systemctl start repoxplorer-webui
sudo systemctl status repoxplorer-webui

# You can check the webui log via journalctl
sudo journalctl -f
```

## Sanitize author identities

In the example below all contributions for John Doe will be stacked if
the author email field of the GIT commit object is one of the defined
emails.

Edit ~/repoxplorer/local/share/repoxplorer/idents.yaml

```YAML
---
- name: John Doe
  emails:
    - john.doe@server
    - jdoe@server
```

## Metadata automatic indexation

In addition to the standard Git object fields, the indexer will detect
metadata such as:

- close-bug: #123
- implement-feature: bp-new-scheduler

All "key: value" that match the following default regex will be indexed:

```
'^([a-zA-Z-0-9_-]+):([^//].+)$'
```

Furthermore in the projects.yaml file it is possible to specify
custom capturing regexs to extract metadata that does not
follow to the default regex.

All regexs specified in the *parsers* key will be executed on
each commit message line. You need to have two captured elements
and the first one will be used as the key the second one as
the value.

```YAML
templates:
- name: default
  uri: https://github.com/openstack/%(name)s
  branch: master
  gitweb: https://github.com/openstack/%(name)s/commit/%%(sha)s
  parsers:
  - .*(blueprint) ([^ .]+).*
```

## Use the commits.json REST endpoint to query the internal DB

This endpoint is used by the UI to fetch commits listing according
to the filters you have setup in the UI but the endpoint can be also used
outside of the UI. Here are some examples about how to use it:

```
# Return all commits from repositories included in the designate project
curl "http://localhost:8080/commits.json?pid=designate"

# Return all commits from repositories included into the designate project that
# have a metadata "Closes-bug" (whatever the field value)
curl "http://localhost:8080/commits.json?pid=designate&metadata=Closes-Bug:*"

# Return all commits from all repositories that have the
# metadata "implement-feature" that match "bp-new-scheduler"
curl "http://localhost:8080/commits.json?metadata=implement-feature:bp-new-scheduler"

# Return all commits from all repositories that have the
# metadata "implement-feature" that match "bp-new-scheduler" or
# "implement" that match "bp-new-scheduler"
curl "http://localhost:8080/commits.json?metadata=implement-feature:bp-new-scheduler,implement:bp-new-scheduler"
```

Available arguments are:
- fromdate: epoch
- todate: epoch
- limit: amount of result returned by page (default: 10)
- start: page cursor
- pid: project name as configured in projects.yaml
- tid: tag as configured in the projects.yaml
- cid: contributor id

## Run tests

```Shell
./bin/el-start.sh
tox
```

## Contribute

RepoXplorer is new and should be considered Alpha ! Feel free to help !
Look at the feature requests list on the Github issue tracker:

- [Feature requests](https://github.com/morucci/repoxplorer/issues?q=is%3Aopen+is%3Aissue+label%3Aenhancement)

If you find an issue please fill a bug report here:

- [Report an issue](https://github.com/morucci/repoxplorer/issues/new)

RepoXplorer is hosted on this Gerrit instance [Software Factory] (http://softwarefactory-project.io)
a contribution should be done via Gerrit instead of using the Pull Request system of Github.

If you want to help:

```Shell
git clone http://softwarefactory-project.io/r/repoxplorer
git review -s # You should have login on Software Factory using your Github identity first
```

Your local copy is now configured. Please read the following instructions to
learn about Git review sub-command [git-review] (http://softwarefactory-project.io/docs/submitpatches.html#initialize-the-git-remote-with-git-review).

```
# make some changes
git add -a
git commit # local commit your changes
git review # propose your changes on Gerrit
```
