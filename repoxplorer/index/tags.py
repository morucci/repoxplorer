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
    "sha": {"type": "string", "index": "not_analyzed"},
    "date": {"type": "date", "format": "epoch_second"},
    "name": {"type": "string", "index": "not_analyzed"},
    "project": {"type": "string", "index": "not_analyzed"},
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
                                body=self.mapping)

    def add_tags(self, source_it):
        def gen(it):
            for source in it:
                d = {}
                d['_index'] = self.index
                d['_type'] = self.dbname
                d['_op_type'] = 'create'
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

    def get_tags(self, projects, fromdate=None, todate=None):

        filter = {
            "bool": {
                "must": [],
                "should": [],
                }
            }

        for project in projects:
            should_project_clause = {
                "bool": {
                    "must": []
                }
            }
            should_project_clause["bool"]["must"].append(
                {"term": {"project": project}}
            )
            filter["bool"]["should"].append(should_project_clause)

        body = {
            "filter": filter
        }

        body["filter"]["bool"]["must"].append(
            {
                "range": {
                    "date": {
                        "gte": fromdate,
                        "lt": todate,
                    }
                }
            }
        )

        return [t for t in scanner(self.es, query=body,
                index=self.index, doc_type=self.dbname)]
