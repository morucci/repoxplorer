# RepoXplorer - Statistics explorer for Git repositories

- **Demo instance**: [demo](http://5.135.161.134/repoxplorer-demo/).
- **Last release**: [1.1.1](https://github.com/morucci/repoxplorer/releases/tag/1.1.1).

RepoXplorer provides a web UI to browse statistics about:

- projets (composed of one or multiple repositories)
- contributors
- groups of contributors

Stats for a project are such as:

- commits and authors count
- date histogram of commits
- date histogram of authors
- top authors by commits
- top authors by lines modified

Stats for a contributor or a group are such as:

- commits, lines modified and projects count
- date histogram of commits
- date histogram of authors (only for group)
- top projects by commits
- top projects by lines modified

Filters can be used to refine stats by:

- dates boundaries
- releases or tags dates
- repositories
- metadata (grabbed from commit message eg. fix-bug: 12)

RepoXplorer is composed of:

- a YAML configuration file (to define repositories to index)
- a Git indexer service
- a wsgi app
- ElasticSearch as backend

RepoXplorer is the right tool to continuously watch and index your
repositories like for instance your Github organization.

## Quickstart script

**repoxplorer-quickstart.sh** is a script to easily run repoXplorer locally without
the need to install services on your system. No root access is needed for the setup
and the installation is self-contained in **$HOME/.cache/repoxplorer**.

This quickstart script only support Github.

The Java Runtime Environment as well as Python and Python virtualenv are the only
dependencies needed.

Let's try to index the repoxplorer repository from the morucci Github organization.

```
curl -O https://raw.githubusercontent.com/morucci/repoxplorer/master/repoxplorer-quickstart.sh
chmod +x ./repoxplorer-quickstart.sh
./repoxplorer-quickstart.sh morucci repoxplorer
firefox http://localhost:51000
```

To index the whole organization do not append the repository name.

## All In One Docker container

A repoXplorer Docker image exists. Check it out there [repoXplorer docker image](https://hub.docker.com/r/morucci/repoxplorer/).
This is a all-in-one container that bundles ElasticSearch + repoXplorer ready to use.

## Installation

The installation process described here is for CentOS 7 only.

### ElasticSearch

repoXplorer relies on ElasticSearch. Below is the installation steps for
ElasticSearch 2.x:

```Shell
sudo rpm --import https://packages.elastic.co/GPG-KEY-elasticsearch
cat << EOF | sudo tee /etc/yum.repos.d/elasticsearch.repo
[elasticsearch-2.x]
name=Elasticsearch repository for 2.x packages
baseurl=https://packages.elastic.co/elasticsearch/2.x/centos
gpgcheck=1
gpgkey=https://packages.elastic.co/GPG-KEY-elasticsearch
enabled=1
EOF
sudo yum install -y elasticsearch java-1.8.0-openjdk
sudo sed -i s/.*ES_HEAP_SIZE=.*/ES_HEAP_SIZE=2g/ /etc/sysconfig/elasticsearch
sudo systemctl enable elasticsearch
sudo systemctl start elasticsearch
```

### Using the RPM

```Shell
# Some dependecies need to be fetched from EPEL
sudo yum install -y epel-release
sudo yum install -y https://github.com/morucci/repoxplorer/releases/download/1.1.1/repoxplorer-1.1.1-1.el7.centos.noarch.rpm
# Fetch needed web assets (JQuery, JQuery-UI, Bootstrap, ...)
sudo /usr/bin/repoxplorer-fetch-web-assets -p /usr/share/repoxplorer/public/
# Enable and start services
sudo systemctl enable repoxplorer
sudo systemctl enable repoxplorer-webui
sudo systemctl start repoxplorer
sudo systemctl start repoxplorer-webui
```

Then open a Web browser to access http://localhost:51000

The default index.yaml configuration file is available in /etc/repoxplorer.
Please then follow the [Configuration section](#configuration).

### Using a Python virtualenv

This is method to follow especially if you intend to try the master version.

```Shell
yum install -y python-virtualenv libffi-devel openssl-devel python-devel git gcc
mkdir git && cd git
git clone https://github.com/morucci/repoxplorer.git
cd repoxplorer
virtualenv ~/repoxplorer
. ~/repoxplorer/bin/activate
pip install -U pip
pip install -r requirements.txt
python setup.py install
./bin/repoxplorer-fetch-web-assets
```

#### Start the web UI

```Shell
cat > ~/start-ui.sh << EOF
gunicorn_pecan --workers 1 --chdir / -b 0.0.0.0:51000 \
 --name repoxplorer ~/repoxplorer/local/share/repoxplorer/config.py
EOF
chmod +x ~/start-ui.sh
~/start-ui.sh
```

Then open a Web browser to access http://localhost:51000

#### Start the indexer

```Shell
python ~/repoxplorer/bin/repoxplorer-indexer
```

In order to run the indexer continuously you can use the command's
argument "--forever".

#### Install systemd unit file for the web UI:

You can install the systemd unit file for the web UI.
Be sure to set the correct path to the uwsgi tool, the config.py file
and web assets as this unit file expect repoXplorer installed outside
of a virtualenv.

```
sudo cp etc/repoxplorer-webui.service /usr/lib/systemd/system/repoxplorer-webui.service

sudo systemctl daemon-reload
sudo systemctl start repoxplorer-webui
sudo systemctl status repoxplorer-webui

# You can check the webui log via journalctl
sudo journalctl -f
```

#### Install systemd unit file for the indexer

```
sudo cp etc/repoxplorer.service /usr/lib/systemd/system/repoxplorer.service
# Be sure to set the correct path to the repoxplorer-indexer script

sudo systemctl daemon-reload
sudo systemctl start repoxplorer
sudo systemctl status repoxplorer

# You can check the indexer log via journalctl
sudo journalctl -f
```

## Quickstart helpers

### Index a Github organization

RepoXplorer comes with an helper to create a yaml file for
from indexing a Github organization. The yaml file can
then be moved to the configuration directory of repoXplorer.

```
repoxplorer-github-organization --org <orgname>
mv <orgname>.yaml ~/repoxplorer/local/share/repoxplorer/
# or
mv <orgname>.yaml /etc/repoxplorer/
```

Using the *--repo* argument in addition to the *--org* argument
will create the yaml file for indexing a single repository.

## Configuration

If RepoXplorer has been installed in a virtualenv then
replace /etc/repoxplorer to ~/repoxplorer/local/share/repoxplorer.

### How to define projects to index

Below is an example of a yaml file, note that *Barbican* and *Swift*
projects are composed of two Git repositories each, a server and a client.

Edit /etc/repoxplorer/myconf.yaml to add projects you want to index.

```YAML
---
project-templates:
  default:
    uri: https://github.com/openstack/%(name)s
    branches:
    - master
    - stable/mitaka
    - stable/newton
    - stable/ocata
    gitweb: https://github.com/openstack/%(name)s/commit/%%(sha)s

projects:
  Barbican:
    description: The Barbican project
    repos:
      barbican:
        template: default
      python-barbicanclient:
        template: default
  Swift:
    description: The Swift project
    repos:
      swift:
        template: default
      python-swiftclient:
        template: default
```

After a change in this file you can start the Git indexer manually or
let the indexer daemon reads the file (every minute) and handles changes.

#### Advanced configuration

The **branches** key of a template definition permits to defines which
branches to index. This key expects a list of branches name.

A list of tags can be given to each Git repositories. This tag concept
should not be understood as Git tags but only as a way to mark
Git repositories. For example tags like 'documentation', 'librairies',
packaging, ...) could be considered. Tags defined at repositories level
will be appended to those defined at the template level.

```YAML
project-templates:
  default:
    uri: https://github.com/openstack/%(name)s
    branches:
    - master
    tags:
    - openstack

projects:
  Barbican:
    repos:
      barbican:
        templates: default
        tags:
        - language:python
```

If the list of the repository branches differs to the one defined in the
template then you can overwrite it like below.

```YAML
project-templates:
  default:
    uri: https://github.com/openstack/%(name)s
    branches:
    - master

projects:
  Barbican:
    repos:
      barbican:
        templates: default
        branches:
        - devel
        - stable/1.0.x
      python-barbicanclient:
        templates: default
```

A list of **releases** can be defined. It is useful when you want to define
release dates across all repositories defined in a project.
Release dates with %Y-%m-%d format can be defined and will be merged with
detected Git tags dates.

```YAML
project-templates:
  default:
    uri: https://github.com/openstack/%(name)s
    branches:
      - master
    releases:
      - name: 2.0
        date: 2016-12-20

projects:
  Barbican:
    repos:
      barbican:
        template: default
```

A list of paths can be given under the **paths** key. When defined for
project repository then only commits including a file
changed under one of the list of paths will match during statistics
computation. If you want to define a special project *Barbian-Tests*
that is limited to tests directory then:

```YAML
project-templates:
  default:
    uri: https://github.com/openstack/%(name)s
    branches:
      - master

projects:
  Barbican:
    repos:
      barbican:
        template: default
        paths:
        - barbican/tests/
        - barbican/functional-tests/
      python-barbicanclient:
        templates: default
        paths:
        - barbicanclient/tests/
```

It is also possible to define **metadata parsers**. Please refer to
the [Metadata automatic indexation section](#metadata-automatic-indexation).

### Sanitize author identities

An unique author can use multiple emails (identities) when contributing
to a project. The **identities** configuration permits to define
emails that belong to a contributor.

In the example below, contributions from both author emails 'john.doe@server'
and 'jdoe@server' will be stacked for John Doe.

```YAML
---
identities:
  0000-0000:
    name: John Doe
    default-email: john.doe@server.com
    emails:
      john.doe@server.com:
        groups:
          barbican-ptl:
            begin-date: 2016-12-31
            end-date: 2017-12-31
      jdoe@server.com:
        groups: {}
```

Group's membership can be defined via the **groups** key. A group must has
been defined ([Define groups of authors](#define-groups-of-authors)) before use.
Membership bounces can be defined via **begin-date** and **end-date** to declare
a group's membership between given dates (%Y-%m-%d).

When an identity declares a group's membership then that's not needed to
define it again at groups level.

### Define groups of authors

You may want to define groups of authors and be able to compute
stats for thos groups.

```YAML
---
groups:
  barbican-ptl:
    description: Project team leaders of Barbican project
    emails:
      john.doe@server.com:
      jane.doe@server.com:
        begin-date: 2015-12-31
        end-date: 2016-12-31
  barbican-core:
    description: Project team leaders of Barbican project
    emails: {}
  acme:
    description: ACME corp group
    emails: {}
    domains:
      - acme.com
      - acme.org
```

Group's membership is defined via an author email. Bounces can be defined
via **begin-date** and **end-date** to declare a group's membership between
given dates (%Y-%m-%d).

If an identity has been defined with emails part of a defined group then
date bounces will overwrite those defined at the groups level.

To define a group that implicitly include commits of authors from
specific domains use the **domains** key to list domains.


### Metadata automatic indexation

In addition to the standard Git object fields, the indexer detects
metadata such as:

- close-bug: #123
- implement-feature: bp-new-scheduler

All "key: value" that match this default regex will be indexed:

```
'^([a-zA-Z-0-9_-]+):([^//].+)$'
```

Furthermore it is possible to specify custom capturing regexs to
extract metadata that does not follow to the default regex.

All regexs specified in the **parsers** key will be executed on
each commit message line. You need to have two captured elements
and the first one will be used as the key, the second as the value.

```YAML
project-templates:
  default:
    uri: https://github.com/openstack/%(name)s
    branches:
    - master
    gitweb: https://github.com/openstack/%(name)s/commit/%%(sha)s
    parsers:
    - .*(blueprint) ([^ .]+).*
```
Custom capturing regexs must be defined prior to the indexation
of the Git repository it apply.

### Validate the configuration

The command *repoxplorer-config-validate* can be used to check
that yaml definition files follow the right format. Please use
the --config option to target /etc/repoxplorer/config.py
when repoXplorer has been installed via the RPM package.

```Shell
repoxplorer-config-validate
```

## Use the commits.json REST endpoint to query the internal DB

This endpoint is used by the UI to fetch commits listing according
to the filters you have setup in the UI but the endpoint can be also used
outside of the UI. Here are some examples about how to use it:

```Shell
# Return all commits from repositories included in the designate project
curl "http://localhost:51000/commits.json?pid=designate"

# Return all commits from repositories included into the designate project that
# have a metadata "Closes-bug" (whatever the field value)
curl "http://localhost:51000/commits.json?pid=designate&metadata=Closes-Bug:*"

# Return all commits from all repositories that have the
# metadata "implement-feature" that match "bp-new-scheduler"
curl "http://localhost:51000/commits.json?metadata=implement-feature:bp-new-scheduler"

# Return all commits from all repositories that have the
# metadata "implement-feature" that match "bp-new-scheduler" or
# "implement" that match "bp-new-scheduler"
curl "http://localhost:51000/commits.json?metadata=implement-feature:bp-new-scheduler,implement:bp-new-scheduler"
```

Available arguments are:
- fromdate: epoch
- todate: epoch
- limit: amount of result returned by page (default: 10)
- start: page cursor
- pid: project name as configured in projects.yaml
- tid: tag as configured in the projects.yaml
- cid: contributor id


## Contribute

RepoXplorer is new and should be considered Alpha ! Feel free to help !
Look at the feature requests list on the Github issue tracker:

- [Feature requests](https://github.com/morucci/repoxplorer/issues?q=is%3Aopen+is%3Aissue+label%3Aenhancement)

If you find an issue please fill a bug report here:

- [Report an issue](https://github.com/morucci/repoxplorer/issues/new)

RepoXplorer is hosted on this Gerrit instance [Software Factory](http://softwarefactory-project.io)
a contribution should be done via Gerrit instead of using the Pull Request system of Github.

If you want to help:

```Shell
git clone http://softwarefactory-project.io/r/repoxplorer
git review -s # You should have login on Software Factory using your Github identity first
```

Your local copy is now configured. Please read the following instructions to
learn about Git review sub-command [git-review](http://softwarefactory-project.io/docs/submitpatches.html#initialize-the-git-remote-with-git-review).

```
# make some changes
git add -a
git commit # local commit your changes
git review # propose your changes on Gerrit
```

### Run tests

The unittest suite requires a local ElasticSearch server accessible on the
default port 9200/tcp. RepoXplorer is tested with ElasticSearch 2.x.
No specific configuration is needed. The suite uses specific indexes
destroyed and re-created at each run.

```Shell
tox
```

## Contact

Let's join the #repoxplorer channel on freenode.
