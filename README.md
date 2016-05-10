# RepoXplorer

RepoXplorer is a small stats and charts utility for GIT repositories.
Its main purpose is to ease the visualization of stats for one or
more projects.

As lot of projects are composed of multiple sub-projects (server, client,
libraries). RepoXplorer let's you define how a project is composed and
then compute stats across multiple sub-projects.

Furthermore it is possible to define author identities by listing
author' emails and then avoid duplicated author in computed stats.

RepoXplorer relies on ElasticSearch and Pecan. Once the service is
started only a web browser is needed to access the user interface.

## A visual overview of the user interface

![capture 1](https://raw.githubusercontent.com/morucci/repoxplorer/master/imgs/repoxplorer_capt1.png)
![capture 2](https://raw.githubusercontent.com/morucci/repoxplorer/master/imgs/repoxplorer_capt1.png)

## How to install

First install repoxplorer in a virtualenv.

```Shell
virtualenv ~/repoxplorer
. ~/repoxplorer/bin/activate
pip install -r requirements.txt
python setup.py install
```

Install Elasticsearch. Here we use an already "ready to use" Docker
container.

```Shell
~/repoxplorer/bin/el-start.sh
```

Start the RepoXplorer web app.

```Shell
uwsgi --http-socket :8080 --pecan ~repoxplorer/local/share/repoxplorer/config.py
```

## Index a project

A yaml file should be provisioned with the projects you want to index. The
file $prefix/local/share/repoxplorer/projects.yaml is expected to be found.

Below is the default projects.yaml files provided. Note that Barbican project
is composed of two sub-projects: the server and the client.

Edit this file to add projects you want to index.
~repoxplorer/local/share/repoxplorer/projects.yaml.

```YAML
---
- Barbican:
   - name: barbican
     uri: https://github.com/openstack/barbican
     branch: master
   - name: python-barbicanclient
     uri: https://github.com/openstack/python-barbicanclient
     branch: master
```

Then start the GIT indexer manually or configure CRON job. The indexer
will read the projects.yaml file and will index project' commits in the
ElasticSearch DB.

```Shell
python ~repoxplorer/bin/repoxplorer-indexer
```

## Sanitize author identities

In the example below all contributions for John Doe will be stacked if
the author email field of the GIT commit object is one of the defined
emails.

Edit ~repoxplorer/local/share/repoxplorer/idents.yaml

```YAML
---
- name: John Doe
  emails:
    - john.doe@server
    - jdoe@server
```

## Run tests

```Shell
tox
```

## Contribute

RepoXplorer is new and should be considered Alpha ! Feel free to help !
Look at the feature requests list on the Github issue tracker.
