# Copyright 2016-2017, Fabien Boucher
# Copyright 2016-2017, Red Hat
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


import copy
import logging

from pecan import conf

from elasticsearch.helpers import bulk
from elasticsearch.helpers import BulkIndexError
from elasticsearch.helpers import scan as scanner

from repoxplorer import index
from repoxplorer.index import YAMLDefinition
from repoxplorer.index import date2epoch
from repoxplorer.index import users
from datetime import datetime

logger = logging.getLogger(__name__)

groups_schema = """
$schema: http://json-schema.org/draft-04/schema

definitions:
  email:
    anyOf:
      - type: object
        additionalProperties: false
        properties:
          begin-date:
            type: string
          end-date:
            type: string
      - type: "null"

type: object
properties:
  groups:
    type: object
    additionalProperties: false
    patternProperties:
      ^.+$:
        type: object
        additionalProperties: false
        required:
          - description
          - emails
        properties:
          description:
            type: string
          domains:
            type: array
            uniqueItems: true
            items:
              type: string
          emails:
            type: object
            additionalProperties: false
            patternProperties:
              ^.+@.+$:
                $ref: "#/definitions/email"
"""

groups_example = """
groups:
  acme-10:
    description: The group 10 of acme
    emails:
      test@acme.com:
        begin-date: 2016-01-01
        end-date: 2016-01-01
      test2@acme.com:
    domains:
      - acme10.org
      - acme.org
  acme-11:
    description: The group 11 of acme
    emails:
      test@acme.com:
      test2@acme.com:
      test3@acme.com:
"""


class Groups(YAMLDefinition):

    PROPERTIES = {
        "description": {"type": "string"},
        "domains": {"type": "string"},
        "emails": {
            "type": "nested",
            "properties": {
                "email": {"type": "string", "index": "not_analyzed"},
                "begin-date": {"type": "string", "index": "not_analyzed"},
                "end-date": {"type": "string", "index": "not_analyzed"},
            }
        }
    }

    def __init__(self, db_path=None, db_default_file=None,
                 db_cache_path=None, connector=None, dump_yaml_in_index=None):
        self.es = connector.es
        self.ic = connector.ic
        self.index = connector.index
        self.dbname = 'groups'
        self.mapping = {
            self.dbname: {
                "properties": self.PROPERTIES,
            }
        }
        if dump_yaml_in_index:
            YAMLDefinition.__init__(
                self, self.db_path, self.db_default_file, self.db_cache_path)
            issues = self.validate()
            if issues:
                raise RuntimeError(issues)
            self.enrich()
            self.load()

    def _merge(self):
        """ Merge self.data and inherites from default_data
        """
        merged_groups = {}
        for d in self.data:
            groups = d.get('groups', {})
            merged_groups.update(copy.copy(groups))

        self.groups = {}
        if self.default_data:
            self.groups = copy.copy(self.default_data.get('groups', {}))

        self.groups.update(merged_groups)

    def _enrich(self):
        for gid, groups in self.groups.items():
            for email, data in groups['emails'].items():
                if not data:
                    continue
                for key in ('begin-date', 'end-date'):
                    if key in data:
                        data[key] = date2epoch(data[key])
                    else:
                        data[key] = None

    def validate(self):
        """ Validate self.data consistencies for groups
        """
        _, issues = self._check_basic('groups',
                                      groups_schema,
                                      'Group')
        if issues:
            return issues
        # Check uncovered by the schema validator
        for gid, groups in self.groups.items():
            for email, data in groups['emails'].items():
                if not data:
                    continue
                try:
                    for key in ('begin-date', 'end-date'):
                        if key in data:
                            datetime.strptime(data[key], "%Y-%m-%d")
                except Exception:
                    issues.append("Group %s declares email %s "
                                  "membership invalid date %s" % (
                                      gid, email, data))
        return issues

    def manage_bulk_err(self, exc):
        errs = [e['create']['error'] for e in exc[1]]
        if not all([True for e in errs if
                    e['type'] == 'document_already_exists_exception']):
            raise Exception(
                "Unable to create one or more doc: %s" % errs)

    def create(self, docs, type):
        def gen():
            for pid, doc in docs:
                d = {}
                d['_index'] = self.index
                d['_type'] = type
                d['_op_type'] = 'create'
                d['_id'] = pid
                d['_source'] = doc
                yield d
        try:
            bulk(self.es, gen())
        except BulkIndexError as exc:
            self.manage_bulk_err(exc)
        self.es.indices.refresh(index=self.index)

    def delete_all(self):
        def gen(docs, dbname):
            for doc in docs:
                d = {}
                d['_index'] = self.index
                d['_type'] = dbname
                d['_op_type'] = 'delete'
                d['_id'] = doc['_id']
                yield d
        bulk(self.es,
             gen(self.get_all(source=False), self.dbname))
        self.es.indices.refresh(index=self.index)

    def load(self, groups):
        self.delete_all()
        self.create(groups.items(), self.dbname)

    def get_all(self, source=True, type=None):
        query = {
            '_source': source,
            'query': {
                'match_all': {}
            }
        }
        return scanner(self.es, query=query, index=self.index,
                       doc_type=type or self.dbname)

    def get_by_id(self, id, source=True):
        try:
            res = self.es.get(index=self.index,
                              doc_type=self.dbname,
                              _source=source,
                              id=id)
            return res['_source']
        except Exception as e:
            logger.error('Unable to get the doc. %s' % e)

    def exists(self, id):
        return self.es.exists(
            index=self.index, doc_type=self.dbname, id=id)

    def get_groups(self):
        return self.groups

    def get_group_by_id(self, id):
        groups = self.get_groups()
        return id, copy.deepcopy(groups.get(id))
