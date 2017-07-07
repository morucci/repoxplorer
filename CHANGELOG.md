=============
Release Notes
=============

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


