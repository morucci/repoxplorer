# RepoXplorer

RepoXplorer is a small stats and charts utility for GIT repositories.
Its main purpose is to ease the visualization of stats for one or
more project(s) composed of multiple GIT repositories.

As lot of projects are composed of multiple GIT repositories (server,
client, libraries). RepoXplorer let's you describe how a project is composed
and then computes stats across multiple GIT repositories.

Furthermore it is possible to define author identities by listing
author emails and then avoid duplicated authors in computed stats.

RepoXplorer relies on ElasticSearch. Once the service is started only
a web browser is needed to access the user interface.

## A visual overview of the user interface

![capture 1](https://raw.githubusercontent.com/morucci/repoxplorer/master/imgs/repoxplorer.jpg)

## How to install

First install repoxplorer in a virtualenv.

```Shell
virtualenv ~/repoxplorer
. ~/repoxplorer/bin/activate
pip install -r requirements.txt
python setup.py install
```

Install Elasticsearch. Here we use an already "ready to use" Docker
container. But you should definitely use a regular installation
of ElasticSearch.

```Shell
~/repoxplorer/bin/el-start.sh
```

## How to index a list of GIT hosted projects

A yaml file should be provisioned with the projects you want to index. The
file $prefix/local/share/repoxplorer/projects.yaml is expected to be found.

Below is the default projects.yaml files provided. Note that Barbican project
is composed of two GIT repositories: the server and the client.

A list of tags can be given to each GIT repositories. This tag notion
should not be concidered as GIT tags but only as a way to group
GIT repositories.

Edit this file to add projects you want to index.
~/repoxplorer/local/share/repoxplorer/projects.yaml.

```YAML
---
templates:
- name: default
  uri: https://github.com/openstack/%(name)s
  branch: master
  gitweb: https://github.com/openstack/%(name)s/commit/%%(sha)s

projects:
  Barbican:
  - name: barbican
    tags:
      - python
    template: default
  - name: python-barbicanclient
    tags:
      - python
    template: default
```

Then start the GIT indexer manually.

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

If you wante to help by contributing on the code:

```Shell
git clone http://softwarefactory-project.io/r/repoxplorer
git review -s # You should have login on Software Factory using you Github identity first
```

Your local copy is now configured. Please read the following instructions to
learn about git review sub-command [git-review] (http://softwarefactory-project.io/docs/submitpatches.html#initialize-the-git-remote-with-git-review).

```
# make some changes
git add -a
git commit # local commit your changes
git review # propose your changes on Gerrit
```
