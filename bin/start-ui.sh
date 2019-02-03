#!/bin/bash

set -x

config=${1:-config.py}
gunicorn_pecan --workers 3 --chdir / -b 0.0.0.0:51000 --name repoxplorer $config
