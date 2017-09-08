=============
Release Notes
=============

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

