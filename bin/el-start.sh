#!/bin/bash

set -ex

docker run --name el-rxp-test -d -p 9200:9200 million12/elasticsearch
