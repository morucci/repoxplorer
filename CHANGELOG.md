=============
Release Notes
=============

0.6-8
=====

New Features
------------

- Git tags are now indexed. They are discovered auotmatically for each repository indexed. A tags is indexed only if the branch it targets is indexed.

- The project YAML definition permits to defines release dates. This comes in addition to Git tags.

- UI permits to select release dates from a list in the filter box.


Known Issues
------------

- Nothing to report.


Upgrade Notes
-------------

- EL db schema has changed. A key has been renamed. Please wipe the repoxplorer index then run repoxplorer-indexer to repopulate.


Bug Fixes
---------

- Multiple fixes.

