# Copyright 2017, Red Hat
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


import logging

from elasticsearch.helpers import bulk
from elasticsearch.helpers import scan as scanner

logger = logging.getLogger(__name__)

PROPERTIES = {
    "sha": {"type": "keyword"},
    "date": {"type": "date", "format": "epoch_second"},
    "name": {"type": "keyword"},
    "repo": {"type": "keyword"},
}


class Tags(object):
    def __init__(self, connector=None):
        self.es = connector.es
        self.ic = connector.ic
        self.index = connector.index
        self.dbname = 'tags'
        self.mapping = {
            self.dbname: {
                "properties": PROPERTIES,
            }
        }
        if not self.ic.exists_type(index=self.index,
                                   doc_type=self.dbname):
            self.ic.put_mapping(index=self.index, doc_type=self.dbname,
                                body=self.mapping, include_type_name=True)

    def add_tags(self, source_it):
        def gen(it):
            for source in it:
                d = {}
                d['_index'] = self.index
                d['_type'] = self.dbname
                d['_op_type'] = 'index'
                d['_source'] = source
                yield d
        bulk(self.es, gen(source_it))
        self.es.indices.refresh(index=self.index)

    def del_tags(self, id_list):
        def gen(it):
            for i in it:
                d = {}
                d['_index'] = self.index
                d['_type'] = self.dbname
                d['_op_type'] = 'delete'
                d['_id'] = i
                yield d
        bulk(self.es, gen(id_list))
        self.es.indices.refresh(index=self.index)

    def get_tags(self, repos, fromdate=None, todate=None):

        qfilter = {
            "bool": {
                "must": [],
                "should": [],
                }
            }

        for repo in repos:
            should_repo_clause = {
                "bool": {
                    "must": []
                }
            }
            should_repo_clause["bool"]["must"].append(
                {"term": {"repo": repo}}
            )
            qfilter["bool"]["should"].append(should_repo_clause)

        qfilter["bool"]["must"].append(
            {
                "range": {
                    "date": {
                        "gte": fromdate,
                        "lt": todate,
                    }
                }
            }
        )

        body = {
            "query": {
                "bool": {
                    "filter": qfilter
                }
            }
        }

        return [t for t in scanner(self.es, query=body,
                index=self.index, doc_type=self.dbname)]
