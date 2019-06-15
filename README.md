# RepoXplorer - Stats explorer for Git repositories

- **Demo instance**: [demo](https://repoxplorer-demo.okombu.com).
- **Last release**: [1.5.1](https://github.com/morucci/repoxplorer/releases/tag/1.5.1).

The documentation here is for the **master version** of repoXplorer. If you
look for information about the last stable version, then checkout at
version 1.5.1.

RepoXplorer provides a web UI and a REST API to browse git stats such as:

- projects (composed of one or multiple repositories)
- contributors
- groups of contributors

Stats for a project are such as:

- commits and authors count
- date histogram of commits
- date histogram of authors
- top authors by commits
- top authors by lines changed
- top new authors by commits

Stats for a contributor or a group are such as:

- commits, lines changed and projects count
- date histogram of commits
- date histogram of authors (only for group)
- top projects by commits
- top projects by lines changed

Filters can be used to refine stats by:

- dates boundaries
- releases or tags dates
- repositories
- metadata (grabbed from commit message eg. fix-bug: 12)

RepoXplorer is composed of:

- YAML configuration file(s)
- a Git indexer service
- a WSGI application
- an ElasticSearch backend

RepoXplorer is the right tool to continuously watch and index your
repositories like for instance your Github organization.

## Quickstart - Use the RepoXplorer Docker container to index a Github organization

The docker container bundles ElasticSearch + the last repoXplorer version.

This paragraph describes the usage of the container of repoXplorer 1.5.1. Some
commands/options may have changes on the master version. A container for the
master version of repoXplorer is published as well and can be deployed using
`docker-compose -f docker-compose-master.yaml up -d`, please refer to
`docker/aoi-master/README`.

Simply run docker-compose to deploy.

```Shell
git clone --depth 1 https://github.com/morucci/repoxplorer
cd repoxplorer
git checkout 1.5.1
mkdir -p docker-data/conf
docker-compose up -d
firefox http://localhost:51000/index.html
```

Then, locally, use the github helper to create the configuration file. Here we index
the Github organization of the git project.

```Shell
./bin/repoxplorer-github-organization --org git --skip-fork --output-path docker-data/conf/git
```

Alternatively, one can execute this command within the repoxplorer docker image with

```Shell
docker-compose exec repoxplorer bash
repoxplorer-github-organization --org git --skip-fork --output-path /etc/repoxplorer/defs/git
```

Indexation will take between 2 and 5 minutes. Indexation in progress can be seen into
the indexer log file.

```Shell
docker-compose exec repoxplorer bash
tail -f /root/.local/repoxplorer/repoxplorer-indexer.log
```

Repoxplorer will check repositories every 60 seconds for news commits and
index them if any.

Stop the container. Data are stored in docker volumes so you can safely stop
and restart the container. *docker-compose down -v* can be used to remove data.


```Shell
docker-compose down
```

## Standard installation

The installation process described here is for the **master version** of
repoXplorer. If you look for the installation process of the last stable
version, then checkout at version 1.5.1.

This process has been validated with **Fedora 29** but as long as
you have Python 3 and a working ElasicSearch 5.X or 6.X deployment repoXplorer
should work as expected. Feel free to adapt to your Linux distribution.

### ElasticSearch

RepoXplorer relies on ElasticSearch 5.X or 6.X. Below are the installation
steps for ElasticSearch 6.x for a RPM based system:

```Shell
sudo rpm --import https://packages.elastic.co/GPG-KEY-elasticsearch
cat << EOF | sudo tee /etc/yum.repos.d/elasticsearch.repo
[elasticsearch-6.x]
name=Elasticsearch repository for 6.x packages
baseurl=https://artifacts.elastic.co/packages/6.x/yum
gpgcheck=1
gpgkey=https://artifacts.elastic.co/GPG-KEY-elasticsearch
enabled=1
autorefresh=1
type=rpm-md
EOF
sudo yum install -y elasticsearch java-1.8.0-openjdk
sudo systemctl enable elasticsearch
sudo systemctl start elasticsearch
```

### Using a Python virtualenv

This is method to follow especially if you intend to try the master version.

```Shell
sudo yum install -y python-virtualenv libffi-devel openssl-devel python-devel git gcc
mkdir git && cd git
git clone https://github.com/morucci/repoxplorer.git
cd repoxplorer
virtualenv ~/repoxplorer
. ~/repoxplorer/bin/activate
pip install -U pip
pip install -r requirements.txt
python setup.py install
mkdir -p ~/.local/repoxplorer
cp config.py ~/.local/repoxplorer/
repoxplorer-fetch-web-assets --config ~/.local/repoxplorer/config.py
# Install a demo project definition
cp etc/projects.yaml ~/.local/repoxplorer/
```

#### Start the web UI

```Shell
./bin/start-ui.sh ~/.local/repoxplorer/config.py
```

Then open a Web browser to access http://localhost:51000/index.html

#### Start the indexer

```Shell
repoxplorer-indexer --config ~/.local/repoxplorer/config.py
```

In order to run the indexer continuously you can use the command's
argument "--forever". When indexing continuously, it will sleep for
60 seconds between runs.

## Quickstart helpers

### Index a Github organization

RepoXplorer comes with an helper to create a yaml file for
from indexing a Github organization. The yaml file can
then be moved to the configuration directory of repoXplorer.

```
repoxplorer-github-organization --org <orgname>
mv <orgname>.yaml ~/.local/repoxplorer/
```

Using the *--repo* argument in addition to the *--org* argument
will create the yaml file for indexing a single repository.

For private organizations or repositories, you will need to issue a
Token and use the *--token* argument. Tokens can be issued on your
Github account under "Settings > Developer Settings > Personal Access Tokens".
You will need to give the *repo* access.

### Private repositories

The git credential helper won't recognize private repositories by default.
For that, you need to add, your credentials into `repoxplorer-git-credentials-helper`
(if running in container, inside the `/bin/` directory of course).

## Configuration

RepoXplorer will look for the configuration directory *db_path* that is defined
in config.py. The directory is supposed to contain the content definition.

The content definition (projects, groups, contributors) must be defined
in *db_path* as YAML files. Any YAML files in the configuration directory
will be loaded. RepoXplorer will load YAML files and do a basic data update
when definition's keys appears in multiple YAML files. The loading is
performed by alphabetical order.

### Define projects to index

Below is an example of a yaml file, note that *Barbican* and *Swift*
projects are composed of two Git repositories each, a server and a client.

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

The **branches** key of a template definition permits to define which
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
release dates across all repositories defined in a project or for a specific
repository.
Release dates with %Y-%m-%d format can be defined and will be merged with
detected Git tags dates.

Furthermore the **index-tags** flag could be set to **False** to tell the
indexer to skip repositories tags indexation. Also the indexer will make sure to
wipe already indexed tags for the project's repositories.

```YAML
project-templates:
  default:
    uri: https://github.com/openstack/%(name)s
    branches:
      - master
    releases:
      - name: 2.0
        date: 2016-12-20
    index-tags: false

projects:
  Barbican:
    releases:
      - name: Ocata
        date: 2017-02-22
    repos:
      barbican:
        template: default
```

A list of paths can be given under the **paths** key. When defined for
project repository then only commits including a file
changed under one of the list of paths will match during statistics
computation. If you want to define a special project *Barbican-Tests*
that is limited to tests directory then:

```YAML
project-templates:
  default:
    uri: https://github.com/openstack/%(name)s
    branches:
      - master

projects:
  Barbican-Tests:
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

A group can be given to the **bots-group** project's attribute. When
set and target an existing group then commits from this group members
are excluded from the project's stats computation.

```YAML
groups:
  ci-bots:
    emails:
      ci@server.com: {}
      langbot@server.com: {}

projects:
  Barbican:
    bots-group: ci-bots
    repos:
      barbican:
        template: default
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

Group's membership can be defined via the **groups** key. A group must have
been defined ([Define groups of authors](#define-groups-of-authors)) before use.
Membership bounces can be defined via **begin-date** and **end-date** to declare
a group's membership between given dates (%Y-%m-%d).

When an identity declares a group's membership then that's not needed to
define it again at groups level.

### Define groups of authors

You may want to define groups of authors and be able to compute
stats for those groups.

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

- closes-bug: #123
- Co-Authored-By: John Doe <john.doe@domain.com>

The full list of matching regexps is defined in indexer/git/metadata_re.py.
Do not hesitate to propose additional regexp if relevant.

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
that yaml definition files follow the right format.

```Shell
repoxplorer-config-validate --config ~/.local/repoxplorer/config.py
```

## REST API endpoints

### Endpoints

All endpoints can be called with or without the suffix *.json*. If called without
the *.json* suffix then the request's header *Accept: application/json* must be set.

Some endpoints can return CSV data by adding the suffix *.csv* or without the suffix
but by adding the request's header *Accept: text/csv* (curl -H "accept: text/csv").

See [below](#parameters) for available parameters. Keep in mind that some
parameters are mandatory, while some others are optional or only available
for certain calls.

#### /api/v1/status/status

This endpoint permits to retrieve the platform status.

```Shell
curl "http://localhost:51000/api/v1/status/status"
```
```Python
{
    "customtext": "",
    "projects": 2,
    "repos": 4,
    "users_endpoint": False,
    "version": "1.5.1"
}
```

#### /api/v1/projects/projects

This endpoint permits to retrieve defined projects.

```Shell
curl "http://localhost:51000/api/v1/projects/projects"
```

```Python
{
    "projects": {
        "Barbican": {
            "description": "The barbican project",
            "repos": [
                {
                    "branch": "master",
                    "gitweb": "https://github.com/openstack/barbican/commit/%(sha)s",
                    "name": "barbican",
                    "parsers": [],
                    "releases": [],
                    "tags": [],
                    "uri": "https://github.com/openstack/barbican"
                },
                {
                    "branch": "stable/ocata",
                    "gitweb": "https://github.com/openstack/barbican/commit/%(sha)s",
                    "name": "barbican",
                    "parsers": [],
                    "releases": [],
                    "tags": [],
                    "uri": "https://github.com/openstack/barbican"
                },
                {
                    "branch": "master",
                    "gitweb": "https://github.com/openstack/python-barbicanclient/commit/%(sha)s",
                    "name": "python-barbicanclient",
                    "parsers": [],
                    "releases": [],
                    "tags": [],
                    "uri": "https://github.com/openstack/python-barbicanclient"
                },
                {
                    "branch": "stable/ocata",
                    "gitweb": "https://github.com/openstack/python-barbicanclient/commit/%(sha)s",
                    "name": "python-barbicanclient",
                    "parsers": [],
                    "releases": [],
                    "tags": [],
                    "uri": "https://github.com/openstack/python-barbicanclient"
                }
            ]
        }
    },
    "tags": [],
}
```

The **pid** parameter can be passed to request only a project.


```Shell
curl "http://localhost:51000/api/v1/projects/projects?pid=Barbican"
```

```
{"Barbican": {
    "description": "The barbican project",
    "repos": [
        {
            "branch": "master",
            "gitweb": "https://github.com/openstack/barbican/commit/%(sha)s",
            "name": "barbican",
            "parsers": [],
            "releases": [],
            "tags": [],
            "uri": "https://github.com/openstack/barbican"
        },
        ...
    ]
}}
```

#### /api/v1/projects/repos

This endpoint permits to retrieve repositories for a project or tag.

```Shell
curl "http://localhost:51000/api/v1/projects/repos?pid=Barbican"
```

```Python
[
    {
        "branch": "master",
        "gitweb": "https://github.com/openstack/barbican/commit/%(sha)s",
        "name": "barbican",
        "parsers": [],
        "releases": [],
        "tags": [],
        "uri": "https://github.com/openstack/barbican"
    },
    ...
]
```

#### /api/v1/infos/infos

This endpoint is used to fetch project, contributor, group or tag
general information.

```Shell
curl "http://localhost:51000/api/v1/infos/infos?cid=DwAQCBtCFg0WDg4FLAYFBg0SBQ0XAUsFDhg-"
```
```Python
{
    "authors_amount": 1,
    "commits_amount": 13,
    "duration": 33695365,
    "first": 1401312787,
    "last": 1435008152,
    "line_modifieds_amount": 4180,
    "ttl_average": 184525
}
```

This endpoint can also output to CSV.

```Shell
curl "http://localhost:51000/api/v1/infos/infos.csv?cid=DwAQCBtCFg0WDg4FLAYFBg0SBQ0XAUsFDhg-"
# or
curl -H "accept: text/csv" "http://localhost:51000/api/v1/infos/infos?cid=DwAQCBtCFg0WDg4FLAYFBg0SBQ0XAUsFDhg-"
```
```
last,authors_amount,commits_amount,ttl_average,duration,line_modifieds_amount,first
1435008152,1,13,184525,33695365,4180,1401312787
```

#### /api/v1/infos/contributor

This endpoint is used to fetch contributor-specific information. Note the **cid** parameter is
mandatory.

```Shell
curl "http://localhost:51000/api/v1/infos/contributor?cid=DwAQCBtCFg0WDg4FLAYFBg0SBQ0XAUsFDhg-"
```
```Python
{ "name": "John Doe",
  "mails_amount": 1,
  "gravatar": "b726b19f8e7c2e23e403e4b5d3ab4508",
}
```

This endpoint can also output to CSV.

```Shell
curl "http://localhost:51000/api/v1/infos/contributor.csv?cid=DwAQCBtCFg0WDg4FLAYFBg0SBQ0XAUsFDhg-"
# or
curl -H "accept: text/csv" "http://localhost:51000/api/v1/infos/contributor?cid=DwAQCBtCFg0WDg4FLAYFBg0SBQ0XAUsFDhg-"
```
```
gravatar,mails_amount,name
a08de2c8fe4fb685409091d3b6dbd0bf,1,John Doe
```

#### /api/v1/commits/commits

This endpoint is used to fetch commits.

Examples:

```Shell
curl "http://localhost:51000/api/v1/commits/commits.json?pid=Barbican&limit=1"
```
```Python
[
    1,
    2214,
    [
        {
            "Change-Id": [
                "I03080db776eb4c9c2991eca8f5df43f74eb6bf24"
            ],
            "author_date": 1507229976,
            "author_email_domain": "lists.openstack.org",
            "author_gravatar": "5718d97082d0499d42ea0a291c46ec40",
            "author_name": "OpenStack Proposal Bot",
            "ccid": "CxUDDwYYFQcOSwgbCgYFJQoIBhgHSgoWBBsfAAUGDU8aHhM-",
            "cid": "CxUDDwYYFQcOSwgbCgYFJQoIBhgHSgoWBBsfAAUGDU8aHhM-",
            "commit_msg": "Updated from global requirements",
            "committer_date": 1507229976,
            "committer_gravatar": "5718d97082d0499d42ea0a291c46ec40",
            "committer_name": "OpenStack Proposal Bot",
            "files_list": [
                "requirements.txt"
            ],
            "gitwebs": [
                "https://github.com/openstack/python-barbicanclient/commit/77eedac597fb99745751a049a11d0719c4b67a85"
            ],
            "line_modifieds": 2,
            "merge_commit": false,
            "metadata": [
                "Change-Id"
            ],
            "repos": [
                "python-barbicanclient:master"
            ],
            "sha": "77eedac597fb99745751a049a11d0719c4b67a85",
            "ttl": "0:00:00"
        }
    ]
]
```

#### /api/v1/tops/authors/bycommits

This endpoint is used to fetch the top authors list by the amount of commits.
It makes more sense to use it with the **pid** or **tid** parameter.

```Shell
curl "http://localhost:51000/api/v1/tops/authors/bycommits?pid=Barbican"
```
```Python
[
    {
        "amount": 73,
        "cid": "CxUDDwYYFQcOSwgbCgYFJQoIBhgHSgoWBBsfAAUGDU8aHhM-",
        "gravatar": "5718d97082d0499d42ea0a291c46ec40",
        "name": "OpenStack Proposal Bot"
    },
    {
        "amount": 39,
        "cid": "AAoTBhkNB0oIAw8RBQ4FBwcNNR4VBw4VERQPEUoGCQw-",
        "gravatar": "ae4be8ffcc6d487934c3df3d3708049a",
        "name": "Douglas Mendizabal"
    },
    {
        "amount": 35,
        "cid": "BRcHEh0LHAsXAxgGBB0kAgsAHABaBwoL",
        "gravatar": "0ac9841e2c93f631d5f5d88f2aed0910",
        "name": "Arash Ghoreyshi"
    },
    ...
]
```

This endpoint can also output to CSV.

```Shell
curl "http://localhost:51000/api/v1/tops/authors/bycommits.csv?pid=Barbican"
```
```
amount,gravatar,name,cid
73,5718d97082d0499d42ea0a291c46ec40,OpenStack Proposal Bot,CxUDDwYYFQcOSwgbCgYFJQoIBhgHSgoWBBsfAAUGDU8aHhM-
39,ae4be8ffcc6d487934c3df3d3708049a,Douglas Mendizabal,AAoTBhkNB0oIAw8RBQ4FBwcNNR4VBw4VERQPEUoGCQw-
35,0ac9841e2c93f631d5f5d88f2aed0910,Arash Ghoreyshi,BRcHEh0LHAsXAxgGBB0kAgsAHABaBwoL
...
```

#### /api/v1/tops/authors/bylchanged

This endpoint is used to fetch the top authors list by the amount of lines changed.
It makes more sense to use it with the **pid** or **tid** parameter.

```Shell
curl "http://localhost:51000/api/v1/tops/authors/bylchanged?pid=Barbican"
```
```Python
[
    {
        "amount": 5663,
        "cid": "AAoTBhkNB0oIAw8RBQ4FBwcNNR4VBw4VERQPEUoGCQw-",
        "gravatar": "ae4be8ffcc6d487934c3df3d3708049a",
        "name": "Douglas Mendizabal"
    },
    {
        "amount": 3816,
        "cid": "AgkTGVsNEAUIJgYYDR0ISwUOGA--",
        "gravatar": "ac3cb4707ed65da7764a4b3a9fe825e6",
        "name": "Adam Harwell"
    },
    {
        "amount": 3814,
        "cid": "DgQUExAYWhYEDww1HhUHDhURFA8RSgYJDA--",
        "gravatar": "fec13c0a2aa5f2db76eb72a35cd80be0",
        "name": "Jarret Raim"
    },
    ...
]
```

This endpoint can also output to CSV.

```Shell
curl "http://localhost:51000/api/v1/tops/authors/bylchanged.csv?pid=Barbican"
```
```
amount,gravatar,name,cid
5663,ae4be8ffcc6d487934c3df3d3708049a,Douglas Mendizabal,AAoTBhkNB0oIAw8RBQ4FBwcNNR4VBw4VERQPEUoGCQw-
3816,ac3cb4707ed65da7764a4b3a9fe825e6,Adam Harwell,AgkTGVsNEAUIJgYYDR0ISwUOGA--
3814,fec13c0a2aa5f2db76eb72a35cd80be0,Jarret Raim,DgQUExAYWhYEDww1HhUHDhURFA8RSgYJDA--
...
```

#### /api/v1/tops/projects/bycommits

This endpoint is used to fetch the top projects list by the amount of commits.
It makes more sense to use it with the **cid** or **gid** parameter. Note this endpoint can
also output to CSV. When the CSV endpoint is used with the **inc_repos_detail** parameter,
the project field can contain values separated by ';'. Indeed a ref (reponame:branch) can
be part of multiple projects. Then make sure your CSV loader is properly configured to not
interpret ';' as a separator.

```Shell
curl "http://localhost:51000/api/v1/tops/projects/bycommits.json?cid=CQoUBQcJECQMCAAACwEXEUgCGgE-"
```
```Python
[
    {
        "amount": 56,
        "name": "Swift"
    },
    {
        "amount": 4,
        "name": "Barbican"
    }
]
```
```Shell
curl "http://localhost:51000/api/v1/tops/projects/bycommits.csv?cid=CQoUBQcJECQMCAAACwEXEUgCGgE-"
```
```
amount,name
56,Swift
4,Barbican
```

By using the parameter **inc_repos_detail** the response outputs the
top repositories instead of projects.

```Shell
curl "http://localhost:51000/api/v1/tops/projects/bycommits.json?cid=CQoUBQcJECQMCAAACwEXEUgCGgE-&inc_repos_detail=true"
```
```Python
[
    {
        "amount": 41,
        "name": "swift:master",
        "projects": [
            "Swift"
        ]
    },
    {
        "amount": 39,
        "name": "swift:stable/ocata",
        "projects": [
            "Swift"
        ]
    },
    ...
]
```
```Shell
curl "http://localhost:51000/api/v1/tops/projects/bycommits.csv?cid=CQoUBQcJECQMCAAACwEXEUgCGgE-&inc_repos_detail=true"
```
```
amount,name,projects
41,swift:master,Swift
39,swift:stable/ocata,Swift
...
```

#### /api/v1/tops/projects/bylchanged

This endpoint is used to fetch the top projects list by the amount of lines changed.
It makes more sense to use it with the **cid** or **gid** parameter. Note this endpoint can
also output to CSV. When the CSV endpoint is used with the **inc_repos_detail** parameter,
the project field can contain values separated by ';'. Indeed a ref (reponame:branch) can
be part of multiple projects. Then make sure your CSV loader is properly configured to not
interpret ';' as a separator.

```Shell
curl "http://localhost:51000/api/v1/tops/projects/bylchanged.json?cid=CQoUBQcJECQMCAAACwEXEUgCGgE-"
```
```Python
[
    {
        "amount": 21853,
        "name": "Swift"
    },
    {
        "amount": 205,
        "name": "Barbican"
    }
]
```

```Shell
curl "http://localhost:51000/api/v1/tops/projects/bylchanged.csv?cid=CQoUBQcJECQMCAAACwEXEUgCGgE-"
```
```
amount,name
21853,Swift
205,Barbican
```

By using the parameter **inc_repos_detail** the response outputs the
top repositories instead of projects.

```Shell
curl "http://localhost:51000/api/v1/tops/projects/bylchanged.json?cid=CQoUBQcJECQMCAAACwEXEUgCGgE-&inc_repos_detail=true"
```
```Python
[
    {
        "amount": 20172,
        "name": "swift:master",
        "projects": [
            "Swift"
        ]
    },
    {
        "amount": 20033,
        "name": "swift:stable/ocata",
        "projects": [
            "Swift"
        ]
    },
    ...
]
```

```Shell
curl "http://localhost:51000/api/v1/tops/projects/bylchanged.csv?cid=CQoUBQcJECQMCAAACwEXEUgCGgE-&inc_repos_detail=true"
```
```
amount,name,projects
20172,swift:master,Swift
20033,swift:stable/ocata,Swift
...
```

#### /api/v1/tops/authors/diff

This endpoint takes a reference timeframe (parameters **dfromref**/**dtoref**) and a new timeframe
(parameters **dfrom**/**dto**), and returns the authors in the new timeframe that were not present
in the reference timeframe. In other words, it returns the new contributors to the project in
the specified timeframe.

```Shell
curl "http://localhost:51000/api/v1/tops/authors/diff?pid=Barbican&dfromref=2017-11-01&dtoref=2017-11-05&dfrom=2017-11-06&dto=2017-11-16"
```
This command will return the new contributors between November 6th and November 16th 2017,
using the period from November 1st and November 5th 2017 as a reference.
```Python
[
    {
        "amount": 13,
        "cid": "AAoTBhkNB0oIAw8RBQ4FBwcNNR4VBw4VERQPEUoGCQw-",
        "gravatar": "ae4be8ffcc6d487934c3df3d3708049a",
        "name": "Douglas Mendizabal"
    },
    {
        "amount": 2,
        "cid": "AgkTGVsNEAUIJgYYDR0ISwUOGA--",
        "gravatar": "ac3cb4707ed65da7764a4b3a9fe825e6",
        "name": "Adam Harwell"
    },
    ...
]
```

This endpoint can also output to CSV.

```Shell
curl "http://localhost:51000/api/v1/tops/authors/diff.csv?pid=Barbican&dfromref=2017-11-01&dtoref=2017-11-05&dfrom=2017-11-06&dto=2017-11-16"
```
```
amount,gravatar,name,cid
13,ae4be8ffcc6d487934c3df3d3708049a,Douglas Mendizabal,AAoTBhkNB0oIAw8RBQ4FBwcNNR4VBw4VERQPEUoGCQw-
2,ac3cb4707ed65da7764a4b3a9fe825e6,Adam Harwell,AgkTGVsNEAUIJgYYDR0ISwUOGA--
...
```

#### /api/v1/histo/commits

This endpoint is used to fetch ready to use histogram data about
commits amount.

```Shell
curl "http://localhost:51000/api/v1/histo/commits?pid=Barbican"
```
```Python
[
    {
        "date": "2013-02-01",
        "value": 16
    },
    {
        "date": "2013-03-01",
        "value": 28
    },
    ....
]
```

#### /api/v1/histo/authors

This endpoint is used to fetch ready to use histogram data
authors amount.

```Shell
curl "http://localhost:51000/api/v1/histo/authors?pid=Barbican"
```
```Python
[
    {
        "date": "2013-02-01",
        "value": 1
    },
    {
        "date": "2013-03-01",
        "value": 5
    },
    ...
]
```

#### /api/v1/tags/tags

This endpoint is used to retrieve detected releases (Git tags, or user defined ones).

```Shell
curl "http://localhost:51000/api/v1/tags/tags?pid=Barbican"
```
```Python
[
    {
        "date": 1367962025,
        "name": "0.1.36",
        "repo": "https://github.com/openstack/barbican:barbican",
        "sha": "e2a599872041429ddf1d078092b9da5ab839ed83"
    },
    {
        "date": 1368651959,
        "name": "0.1.43",
        "repo": "https://github.com/openstack/barbican:barbican",
        "sha": "ac5df0080930bcfb0872c40d00a7cb99f2179f09"
    },
    ...
]
```

#### /api/v1/metadata/metadata

This endpoint is used to fetch detected commit's metadata.

```Shell
curl "http://localhost:51000/api/v1/metadata/metadata?pid=Barbican"
```
```Python
{
    "Author": 3,
    "Closes-Bug": 245,
    "Closes-bug": 89,
    "Co-Authored-By": 16,
    "Co-authored-by": 7,
    "Depends-On": 21,
    "Fixes": 7,
    "Implementing": 2,
    "Implements": 102,
    "Partial-Bug": 18,
    "Partial-bug": 2,
    "Partially-Implements": 27,
    "Partially-implements": 17,
    ...
}
```

```Shell
curl "http://localhost:51000/api/v1/metadata/metadata?pid=Barbican&key=Implements"
```
```Python
[
    "blueprint add-authentication-token-support",
    "blueprint add-cas",
    "blueprint add-certificate-to-the-container-type",
    "blueprint add-local-installer-script",
    "blueprint add-metadata-to-secrets",
    "blueprint add-missing-alembic-modules",
    ...
]
```

#### /api/v1/search/search_authors

This endpoint can be used to search a commit's author. The search
is performed against the full name and limited to 100 results.

```Shell
curl "http://localhost:51000/api/v1/search/search_authors?query=john"
```
```Python
{
    "CQAmDxoYWgkL": {
        "gravatar": "957192aaa5b95658443fa90b63e10d6a",
        "name": "John Dickinson"
    },
    "DgMRDhoINBEHEw8BGVpMCwkPEEU-": {
        "gravatar": "67b96b16c256d01f79d0d330382229b3",
        "name": "John Wood"
    },
    "DggFChwCECQCCwAcAFoHCgs-": {
        "gravatar": "3d1233d9f185ca8ccfc84654d5bb1d0a",
        "name": "John McKenzie"
   },
   ...
}
```

#### /api/v1/groups/

This endpoint can be used to retrieve the defined groups, and search for
groups that start with a specific prefix.

```Shell
curl "http://localhost:51000/api/v1/groups/"
```
```Python
{
  "Doe Organization": {
    "domains": [],
    "description": "People from the Doe organization",
    "members": {
      "DhUDDxQsBgEBDgABQhcLCA--": {
        "gravatar": "659d8254ef5235d8a163734889131b0e",
        "name": "John Doe"
      },
      "DgQQCBAeWhQACAA1HhEADQcVWw8bCQ--": {
        "gravatar": "b726b19f8e7c2e23e403e4b5d3ab4508",
        "name": "Doe John"
      }
    },
  },
  "redhatters": {
    "domains": [
      "redhat.com"
    ],
    "description": "People from Red Hat",
    "members": {},
  }
}
```

### Parameters

#### Available parameters for all endpoints

##### Mandatory

Only one of:

- **pid**: project ID as in [projects definitions](#define-projects-to-index).
- **tid**: tag ID as in projects definitions.
- **cid**: contributor ID as in [contributors definitions](#sanitize-author-identities) or
  auto computed ID. Furthermore, the **cid** can be a comma separated list of
  emails. The list of emails must end with a comma.
- **gid**: group ID as in [groups definitions](#define-groups-of-authors).

##### Optionals

- **dfrom**: From date with the format: %Y-%m-%d.
- **dto**: To date with the format: %Y-%m-%d.
- **metadata**: key:value list of metadata grabbed from commit messages.
  example: 'implement-feature:bp-new-scheduler,implement:bp-new-scheduler'
- **inc_merge_commit**: Include merge commits in computation (default is no)
  set in to 'on' to include them.
- **inc_repos**: A list of repository IDs to only include in the computation.
  example: 'barbican:master,python-barbicanclient:master'
- **exc_groups**: group ID as in groups definitions to exclude from
  the computation. Can be used only with **pid** or **tid**.
  Only one group is supported. This parameter is exclusive with **inc_groups**.
- **inc_groups**: group ID as in groups definitions to only include in
  the computation. Can be used only with **pid** or **tid**.
  Only one group is supported. This parameter is exclusive with **exc_groups**.

#### commits endpoint only

- **limit**: amount of results returned by page (default: 10).
- **start**: page cursor (default: 0).

#### metadata endpoint only

- **key**: The metadata key.

#### search endpoint only

- **query**: The query terms. Wildcards are authorized and a logical AND is
  used between terms.

#### Group endpoint only

- **prefix**: Return groups that start by `prefix`.
- **nameonly**: if set to `true`, return only the group names. Otherwise, return all information.
- **withstats**: if set to `true`, return the amount of projects and repos that the group have contributed on.

#### tops/projects endpoint only

- **inc_repos_detail**: Set to *true* or unset to include or not
  repositories details in the response.
- **limit**: Max amount of items returned (default: 10).

#### tops/authors endpoint only

- **limit**: Max amount of items returned (default: 10).

#### tops/authors/diff endpoint only

- **dfromref**: Start of the reference period to use when getting new contributors, using the format: %Y-%m-%d.
- **dtoref**: End of the reference period to use when getting new contributors, using the format: %Y-%m-%d.
- **limit**: Max amount of items returned (default: 10).

## Contribute

Feel free to help ! I'll be happy to accept any contributions.

If you want to propose a change, ask for a feature, say you like repoXplorer or
report an issue please fill Github issue:

- [Report an issue](https://github.com/morucci/repoxplorer/issues/new)

RepoXplorer is hosted and developed via this Gerrit instance [Software Factory](https://softwarefactory-project.io).
Contributions should preferably be done via Gerrit but I will accept them on Github too :).

If you want to help via Github then use the regular Github workflow.
Below are instructions to follow if your prefer to use Gerrit:

```Shell
git clone https://softwarefactory-project.io/r/repoxplorer
git review -s # You should have login on Software Factory using your Github identity first
```

Your local copy is now configured. Please read the following instructions to
learn about Git review sub-command [git-review](https://softwarefactory-project.io/docs/submitpatches.html#initialize-the-git-remote-with-git-review).

```
# make some changes
git add -a
git commit # local commit your changes
git review # propose your changes
```

### Run tests

The unittest suite requires a local ElasticSearch server accessible on the
default port 9200/tcp. RepoXplorer is tested with ElasticSearch 5.X and 6.X.
No specific configuration is needed. The suite uses specific indexes
destroyed and re-created at each run.

```Shell
# First install required system libraries
sudo yum install -y python-virtualenv libffi-devel openssl-devel python3-devel git gcc python-tox
# Then run the test suite
tox
```

## Contact

Let's join the #repoxplorer channel on freenode.
