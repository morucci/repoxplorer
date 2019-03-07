=============
Release Notes
=============

Master
======

RepoXplorer is now only Python 3 compatible. Version 3.6 and 3.7 are known
to work and are tested in the CI. Python 2.7 support has been removed.

Support of ElasticSearch 2.X have been removed. Support for ElasticSearch
5.X and 6.X have been added and are tested in the CI.

New features
------------

- Added an account deletion button in the user home page.
- Allow project's releases definition at project level.
- Support of ElasticSearch 5.X and 6.X.
- The catch all metadata regexp has been removed in favor of
  pre-defined regexps matching the most frequent metadatas.

Bug Fixes
---------

Other Notes
-----------

- Removed the cache system for projects. Now all projects are dumped
  and queried from the Elastic index.
- add *db_cache_path* in config to specify directory where to store
  cache files.
- Removed support of ElasticSearch 2.X.


1.4.0
=====

New features
------------

- add indexer cli option *--clean-orphan* to clean no longer
  referenced refs and tags.
- add *index-tags* attribute in project-template definition. This
  tells the indexer to not index repositories tags in the DB.
- add beta feature meta-ref to handle projects composed of
  thousands of repository. For now this feature remain not
  documented.
- add CSV support to infos/contributor endpoint.
- add bots-group project attribute that can be used to
  define project' bots and exclude bots' commits from
  stats results.
- the *pid* parameter can be passed to the projects endpoint.

Bug Fixes
---------

- fix contributors search results not sorted by alphabetical order.
- fix "To date" computation to include the selected day (also fix the top computation).
- fix project page jumbotron link cut when name is multi words.
- fix groups endpoint that ignored dto/dfrom.
- fix project info box not computed based on filters.

Other Notes
-----------

- no longer use /tmp for the seen_refs cache instead store it in db_path.
- ui: change button style of the filter box.
- ui: specify that search is done on author's full name and wildcards authorized
  in the search page.
- api: limit authors search results to 100 items.
- refs cleaner removes repository related tags (from tags db) if it no longer
  exists in project definition.
- discard 1970-01-01 commits from stats results.
- improved groups endpoint response time when withstats to True.

1.3.1
=====

This release mainly brings some performance improvements, and a security fix.

New features
------------

- api/tops: Add the limit attribute to the tops/projects endpoint
- ui: Complete the user setting page - enable bounced group memberships

Bug Fixes
---------

- indexer: prevent to get stuck in case of private repositories on Github
- api/groups: Fix missing domains args in filter

Other Notes
-----------

- indexer: only use git bare repositories for repositories clones.
- indexer: cleaner use delete by bulk to save memory
- ui: gravatar responsive
- ui: escape html for user-controlled input


1.3.0
=====

This release brings some performance improvements and a user backend.

New features
------------

- Add inc_groups query parameter to limit stat computing to only specific groups
- Add users backend and user home page. This is a beta feature that needs
  to be coupled with an authentication layer that will set the REMOTE-USER
  header.
- Indexer auto-detects commits objects to clean from the ELK backend by comparing
  to the refs defined in projects.yaml.

Bug Fixes
---------

- Custom elasticsearch index name was partially taken in account
- Top controller ignored the metadata filter

Other Notes
-----------

- Improved indexation of repositories by doing ELK indexing at each bulk read
- Improved metadata endpoint by computing most common keyword on a limited set
- Improved indexation by adding a step of check if tip of branch changed
- Improved tops/diff endpoint by discovering authors full name at the
  end of the compute process.


1.2.0
=====

This release features a complete and documented REST API where all repoXplorer query types are exposed. The bundled web UI has been refactored to fully used the REST API. A new endpoint to request new contributors during a period compared to a reference period has been implemented. This feature is exposed in the web UI. Finally lot of small improvements have been merged but not listed in this changelog.


New Features
------------

- Most of API endpoint can output to csv in addition to json.

- Add the infos API endpoint.

- Add version API endpoint.

- Add status API endpoint.

- Add the projects API endpoint.

- Add the tops/authors tops/projects API endpoints.

- Add the top/authors/diff endpoint.

- A new REST endpoint infos/contributor has been added

- Make the UI fully uses the REST API and remove make templating.

- tops authors/diff endpoints take an optional limit parameter.

- project pages have a new tool box to display new authors since a date or release date.


1.1.1
=====

New Features
------------

- repoxplorer-github-organization adds a --repo argument to index a single repository.

- add repoxplorer-quickstart.sh to ease on-boarding on repoXplorer.


Bug Fixes
---------

- Prevent the git indexer to uselessly fetch same pack at each run. Bug seen on centos 7.

- Fix get stat by tag that was broken by the recent project schema change.

- Fix manual release definition that was broken by the recent project schema change.

- Fix mandatory usage of a template when defining a repo.

- Fix 500 error when defining a project w/o a gitweb link.


1.1.0
=====

New Features
------------

- Refactoring of the projects listing page to improve the layout. Logo and description can be provided via project definition. Thus definition file format has evolved. Please refer to the upgrade section.


Upgrade Notes
-------------

- Project definition format has changed to include a description and a logo attribute. Repos are now defined under the repos key. The script repoxplorer/index/upgrade/1.0.0_1.1.0.py can be used to update file in place.


Other Notes
-----------

- Change from uwsgi to gunicorn as the recommanded WSGI app wrapper


1.0.2
=====

Bug Fixes
---------

- repoxplorer-config-validate (YAML validation) no longer requires EL to be up and running.


1.0.1
=====

Bug Fixes
---------

- Fix yaml backend cache path that won't be writable in /etc/repoxplorer (installed by package)


1.0.0
=====

New Features
------------

- Project and Tag pages get a new contributors count histogram

- REST endpoints histo/commits and histo/authors have been added

- The group page display partial result and an index is displayed on top.

- A group definition can maps a list of mail domains to implicitly group commits of from specific author's mail domains.

- Partial group membership date bounces can be now defined (eg. just begin-date) when still membership.

- contributor and group pages own a new by project filter.

- Projects definition can include a list of paths under the paths key. This limit statistics computation to those paths.

- Improve datepicker configuration.

- Add progress indicators.

- Add authors histo on the group page.

- The YAML backend use cache files to speedup loading large YAML definitions.


Upgrade Notes
-------------

- The database schema has been modified to include author mail domain and commit modified path. The database should be wiped and re-indexed after the upgrade.


0.9.0
=====

New Features
------------

- Add a welcome page where a custom HTML string can be embedded.

- Now branches can be defined at repository level and not only at project-template level.


Other Notes
-----------

- Display the repoXplorer version in the UI.

- Remove Dulwish dependency and only be based on Git binary

- Far better performance when parsing and indexing Git repos


0.8.0
=====

New Features
------------

- Better YAML structure to define identities and groups

- Better YAML structure to define projects and project-templates

- Definitions of projects, groups, idents, project-templates can done in multiple files (ending with .yaml).

- Add repoxplorer-config-validate command to check definitions

- Add a groups listing page

- Add a group stats page

- bin/helpers/github/repoxplorer-github-organization has been renamed and now support the new format of projects definition

- bin/helpers/github/repoxplorer-openstack has been renamed and now support the new format of projects definition


Upgrade Notes
-------------

- Old idents.yaml file format is deprecated and need to be refactored manually

- Old projects.yaml file format is deprecated and need to be refactored manually


Bug Fixes
---------

- Fix release date format in projects.yaml file. The format is now %m/%d/%Y.

- Prevent the repoxplorer-indexer to crash when an unexpected error occur


Other Notes
-----------

- Rename tools used to create projects.yaml from a github org and from OpenStack governance file.


0.7.2
=====

Bug Fixes
---------

- Global line modifieds amount was wrongly computed

- Stacked by project commit amount was wrong

- Stacked by project line modified amount was wrong


Other Notes
-----------

- Rework Author/Commiter display in commit listing to improve clarity


0.7.1
=====

Bug Fixes
---------

- directory rights when fetching and installing web assets

- config argument of the indexer tool not took in account


0.7
===

New Features
------------

- Git tags are now indexed. They are discovered auotmatically for each repository indexed. A tags is indexed only if the branch it targets is indexed.

- The project YAML definition permits to define release dates. This comes in addition to Git tags.

- UI permits to select release dates from a list in the filter box.

- The project YAML definition permits to define multiple branches to index for a given repository.


Known Issues
------------

- Nothing to report.


Upgrade Notes
-------------

- EL db schema has changed. A key has been renamed. Please wipe the repoxplorer index then run repoxplorer-indexer to repopulate.

- project.yaml structure has changed. The key 'branch' has been renamed 'branches' and is now a list of branches to index. Please update your projects.yaml file.


Bug Fixes
---------

- Multiple fixes.
