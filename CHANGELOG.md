=============
Release Notes
=============

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


