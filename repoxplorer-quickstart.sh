#!/bin/bash

# Copyright 2017, Fabien Boucher
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

set -e
#version="1.1.0"
version="master"

base="$HOME/.cache/repoxplorer"
dwl="$base/dwl"
elinst="$base/inst/el"
repoxplorerinst="$base/inst/repoxplorer"
el="https://download.elastic.co/elasticsearch/release/org/elasticsearch/distribution/tar/elasticsearch/2.4.0/elasticsearch-2.4.0.tar.gz"
repoxplorer="https://github.com/morucci/repoxplorer/archive/${version}.tar.gz"

function create_directories {
    for d in $base $dwl $elinst $repoxplorerinst; do
        if ! test -d $d; then
            mkdir -p $d
        fi
    done
}

function download_contents {
    for d in $el $repoxplorer; do
        if ! test -f "$dwl/$(basename $d)"; then
            pushd $dwl &> debug.txt
            echo "Fetching $d ..."
            curl --progress-bar -OL $d
            popd &> debug.txt
        fi
    done
}

function extract_contents {
    if ! test -f "$elinst/elasticsearch-2.4.0/bin/elasticsearch"; then
        tar -xzf "$dwl/$(basename $el)" -C "$elinst"
    fi
    if ! test -f "$repoxplorerinst/1.1.0/requirements.txt"; then
        tar -xzf "$dwl/$(basename $repoxplorer)" -C "$repoxplorerinst"
    fi
}

function install_venv {
    if ! test -f $repoxplorerinst/bin/activate; then
        virtualenv $repoxplorerinst
    fi
}

function install_repoxplorer {
    if ! test -f $repoxplorerinst/local/share/repoxplorer/config.py; then
        pip install -U pip
        pip install -r $repoxplorerinst/repoxplorer-${version}/requirements.txt
        pip install $repoxplorerinst/repoxplorer-${version}/
    fi
    if ! test -f $repoxplorerinst/local/share/repoxplorer/public/javascript/bootstrap.min.js; then
        $repoxplorerinst/repoxplorer-${version}/bin/repoxplorer-fetch-web-assets
    fi
}

function stop_el {
    while pgrep -f "org.elasticsearch.bootstrap.Elasticsearch start -d"; do
        pkill -f "org.elasticsearch.bootstrap.Elasticsearch start -d"
        sleep 1
        echo "Waiting for EL to stop ..."
    done
}
function start_el {
    if ! pgrep -f "org.elasticsearch.bootstrap.Elasticsearch start -d"; then
        /home/fabien/.cache/repoxplorer/inst/el/elasticsearch-2.4.0/bin/elasticsearch -d
    fi
    while ! netstat -lptn | grep "127.0.0.1:9200"; do
        echo "Waiting for EL to be fully up ..."
    done
}

function stop_repoxplorer_ui {
    while pgrep -f "gunicorn_pecan"; do
        pkill -f "gunicorn_pecan"
        sleep 1
        echo "Waiting for repoxplorer to stop ..."
    done
}
function start_repoxplorer_ui {
    if ! pgrep -f "gunicorn_pecan"; then
        gunicorn_pecan --workers 1 --chdir / -b 0.0.0.0:51000 \
         --name repoxplorer $repoxplorerinst/local/share/repoxplorer/config.py &
    fi
}

function install_conf_via_helper {
    call="repoxplorer-github-organization --skip-fork --org ${org}"
    if test -n "${repo}"; then
        path="${org}_${repo}"
        call="${call} --repo ${repo} --output-path $repoxplorerinst/local/share/repoxplorer/${path}"
    else
        path="${org}"
        call="${call} --output-path $repoxplorerinst/local/share/repoxplorer/${path}"
    fi
    $call
}

function usage {
    echo "--- USAGE ---"
    echo "This is a quickstart repoXplorer launcher for Github"
    echo ""
    echo "For example in order to index the repository 'repoxplorer' from"
    echo "the 'morucci' organisation from Github run:"
    echo ""
    echo "$0 morucci repoxplorer"
    echo ""
    echo "To stop services run:"
    echo ""
    echo "STOP=1 $0"
    exit 1
}

if test -f debug.txt; then
    rm -f debug.txt
fi

if test -n "$STOP"; then
    echo "Stop repoXplorer UI ..."
    stop_repoxplorer_ui &> debug.txt
    echo "Stop ElasticSearch ..."
    stop_el &> debug.txt
else
    org=$1
    repo=$2
    if test -z "$org"; then
        echo "Please provide the Github organisation name as first argument"
        usage
    fi
    echo "Using $base as path for all data."
    echo "This directory can be removed to fully remove repoXplorer"
    echo ""
    echo "Create cache directories ..."
    create_directories
    echo "Download contents ..."
    download_contents
    echo "Extract contents ..."
    extract_contents
    echo "Create Python virtual environment ..."
    install_venv &> debug.txt
    echo "Activate virtual environment ..."
    source $repoxplorerinst/bin/activate
    echo "Install repoXplorer ..."
    install_repoxplorer &> debug.txt
    echo "Start ElasticSearch ..."
    start_el &> debug.txt
    echo "Install configuration ..."
    install_conf_via_helper
    echo "Start repoXplorer UI ..."
    start_repoxplorer_ui &> debug.txt
    echo "Start repoXplorer indexer ..."
    repoxplorer-indexer
    echo ""
    echo "Open your browser on http://localhost:51000"
fi
