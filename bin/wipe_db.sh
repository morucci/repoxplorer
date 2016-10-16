#!/bin/bash

[ -z "$1" ] && {
    echo "Please pass the index name as argument"
    exit 1
}

curl -XDELETE "http://localhost:9200/$1/"
