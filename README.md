# RepoXplorer

RepoXplorer is a stats and charts utility for Git repositories. Its main
purpose is to ease visualization of statistics for projects composed of one
or multiple Git repositories. Indeed lot of projects are splitted and have
a Git repository by component (server, client, library A, ...) but unfortunately
most of the existing Git statistic tools does not handle that.

RepoXplorer let's you describe how a project is composed and then computes
stats across them. RepoXplorer provides a Web UI to browse statistics easily.
RepoXplorer relies on ElasticSearch for its data backend.

## A visual overview of the user interface

![capture 1](https://raw.githubusercontent.com/morucci/repoxplorer/master/imgs/repoxplorer-plist.jpg)
![capture 2](https://raw.githubusercontent.com/morucci/repoxplorer/master/imgs/repoxplorer-pstats.jpg)
![capture 3](https://raw.githubusercontent.com/morucci/repoxplorer/master/imgs/repoxplorer-cont.jpg)

## How to install

Last release is RepoXplorer [1.0.2](https://github.com/morucci/repoxplorer/releases/tag/1.0.2).
The installation process described here is for CentOS 7 only.

### All In One Docker container

A repoXplorer Docker image exists. Check it out there [repoXplorer docker image](https://hub.docker.com/r/morucci/repoxplorer/).
This is a all-in-one container that bundles ElasticSearch + repoXplorer ready to use.

### ElasticSearch installation

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

### RPM installation of repoXplorer

RepoXplorer has been packaged for CentOS 7 with the EPEL7 repository activated. It is
not in the official EPEL7 repositories but a RPM is available.

Here is the process to follow:

First install the EPEL7 repository.

```Shell
sudo yum install -y epel-release
```

Finally install RepoXplorer:

```Shell
sudo yum install -y https://github.com/morucci/repoxplorer/releases/download/1.0.2/repoxplorer-1.0.2-1.el7.centos.noarch.rpm
# Fetch needed web assets (JQuery, JQuery-UI, Bootstrap, ...)
sudo /usr/bin/repoxplorer-fetch-web-assets -p /usr/share/repoxplorer/public/
# Enable and start services
sudo systemctl enable repoxplorer
sudo systemctl enable repoxplorer-webui
sudo systemctl start repoxplorer
sudo systemctl start repoxplorer-webui
```

Then open a Web browser to access http://localhost:51000

projects.yaml and idents.yaml are available in /etc/repoxplorer. Please
then follow the [Configuration section](#configuration).

### Install repoXplorer in a python virtualenv

This is method to follow if you want to try the last master version.

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

Start the RepoXplorer web UI.

```Shell
cat > ~/start-ui.sh << EOF
gunicorn_pecan --workers 1 --chdir / -b 0.0.0.0:51000 \
 --name repoxplorer ~/repoxplorer/local/share/repoxplorer/config.py
EOF
chmod +x ~/start-ui.sh
~/start-ui.sh
```

Then open a Web browser to access http://localhost:51000

Start the RepoXplorer indexer

```Shell
python ~/repoxplorer/bin/repoxplorer-indexer
```

In order to run the indexer continuously you can use the command
argument "--forever".

#### Install systemd unit file for the web UI

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
repoXplorer from a Github organization. The created file can
then be moved to the configuration directory of repoXplorer.

```
repoxplorer-github-organization --org <orgname>
mv <orgname>.yaml ~/repoxplorer/local/share/repoxplorer/
# or
mv <orgname>.yaml /etc/repoxplorer/
```

## Configuration

If RepoXplorer has been installed in a virtualenv then
replace /etc/repoxplorer to ~/repoxplorer/local/share/repoxplorer/.

### How to index a list of Git hosted projects

Below is an example of projects.yaml, note that Barbican and Swift projects
are composed of two Git repositories, a server and a client.

Edit /etc/repoxplorer/projects.yaml to add projects you want to index.

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
    barbican:
      template: default
    python-barbicanclient:
      template: default
  Swift:
    swift:
      template: default
    python-swiftclient:
      template: default
```

After a change in this file you can start the Git indexer manually or
let the indexer daemon reads the file (every minute) and handles changes.

#### Advanced configuration

The branches key of a template definition permits to defines which
branches to index. This key expects a list of branches name.

A list of tags can be given to each Git repositories. This tag concept
should not be considered as Git tags but only as a way to mark
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
    barbican:
      templates: default
      tags:
      - language:python
```

If a repository's branch(es) are not similar to the one(s) defined in the
template then you can overwrite them.

```YAML
project-templates:
  default:
    uri: https://github.com/openstack/%(name)s
    branches:
    - master

projects:
  Barbican:
    barbican:
      templates: default
      branches:
      - devel
      - stable/1.0.x
    python-barbicanclient:
      templates: default
```

A list of releases can be defined. It is useful when you want to define
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
    barbican:
      template: default
```

A list of paths can be given under the *paths* key. When defined for
project repository definition then only commits that include a file
changed under one of the list of paths will match during statistic
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

It is also possible to define metadata parsers. Please refer to
the [Metadata automatic indexation section](#metadata-automatic-indexation).

### Sanitize author identities

It often happens authors use mulitple identities (multiple emails) when
they contribute to a project. You can use the file idents.yaml to define
emails that belong to a contributor. RepoXplorer will use that file to
group contributions with multiple emails under a single identity.

In the example below contributions from both author emails 'john.doe@server'
and 'jdoe@server' will be stacked for John Doe.

Edit /etc/repoxplorer/idents.yaml

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

Group's membership can be defined via the groups key. The group must has
been defined ([Define groups of authors](#define-groups-of-authors)).
Membership bounces can be given via *begin-date* and *end-date* to declare
a group's membership between given dates (%Y-%m-%d).

When an identity announce a group's membership that's not necessary to
define it again at groups level.

### Define groups of authors

You may want to define groups of authors and be able to compute
stats for groups you defined. To do that you have to define groups like below.

Edit /etc/repoxplorer/groups.yaml

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
via *begin-date* and *end-date* to declare a group's membership between
given dates (%Y-%m-%d).

If an identity has been defined with emails part of a defined group then
date bounces will overwrite those defined at the groups level.

To define a group that implicitly include commits of authors from
specific domains use the *domains* key to list domains.


### Metadata automatic indexation

In addition to the standard Git object fields, the indexer will detect
metadata such as:

- close-bug: #123
- implement-feature: bp-new-scheduler

All "key: value" that match the following default regex will be indexed:

```
'^([a-zA-Z-0-9_-]+):([^//].+)$'
```

Furthermore in projects.yaml it is possible to specify
custom capturing regexs to extract metadata that does not
follow to the default regex.

All regexs specified in the *parsers* key will be executed on
each commit message line. You need to have two captured elements
and the first one will be used as the key the second one as
the value.

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

### Run tests

The unittest suite requires a local ElasticSearch server accessible on the
default port 9200/tcp. RepoXplorer is tested with ElasticSearch 2.x.
No specific configuration is needed. The suite uses specific indexes
destroyed and re-created at each run.

```Shell
tox
```
