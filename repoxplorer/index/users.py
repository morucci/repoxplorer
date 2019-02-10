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


import logging
from datetime import datetime

from elasticsearch.exceptions import NotFoundError

from repoxplorer.index import YAMLDefinition
from repoxplorer.index import date2epoch

logger = logging.getLogger(__name__)

idents_schema = """
$schema: http://json-schema.org/draft-04/schema

definitions:
  group:
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
  identities:
    type: object
    additionalProperties: false
    patternProperties:
      ^.+$:
        type: object
        additionalProperties: false
        required:
          - name
          - emails
          - default-email
        properties:
          name:
            type: string
          default-email:
            type: string
            pattern: ^.+@.+$
          emails:
            type: object
            additionalProperties: false
            patternProperties:
              ^.+@.+$:
                type: object
                additionalProperties: false
                properties:
                  groups:
                    type: object
                    additionalProperties: false
                    patternProperties:
                      ^.+$:
                        $ref: "#/definitions/group"
"""

ident_example = """
identities:
  1234-1234:
    name: John Doe
    default-email: jodoe@domain.com
    emails:
      john.doe@domain.com:
        groups:
          acme-10:
            begin-date: 2016-01-01
            end-date: 2016-01-09
          acme-11:
          acme-12:
      jodoe@domain.com:
        groups: {}
  1234-1235:
    name: Jane Doe
    default-email: jane.doe@domain.com
    emails:
      jane.doe@domain.com: {}
      jadoe@domain.com: {}
"""

class Users(YAMLDefinition):

    PROPERTIES = {
        "uid": {"type": "string", "index": "not_analyzed"},
        "name": {"type": "string", "index": "not_analyzed"},
        "default-email": {"type": "string", "index": "not_analyzed"},
        "last_cnx": {"type": "date", "format": "epoch_second"},
        "emails": {
            "type": "nested",
            "properties": {
                "email": {"type": "string", "index": "not_analyzed"},
                "groups": {
                    "type": "nested",
                    "properties": {
                        "group": {
                            "type": "string", "index": "not_analyzed"},
                        "begin-date": {
                            "type": "string", "index": "not_analyzed"},
                        "end-date": {
                            "type": "string", "index": "not_analyzed"}
                        }
                    }
                }
            }
        }

    def __init__(self, db_path=None, db_default_file=None,
                 db_cache_path=None, con=None, dump_yaml_in_index=None):
        self.es = connector.es
        self.ic = connector.ic
        self.index = connector.index
        self.dbname = 'users'
        self.mapping = {
            self.dbname: {
                "properties": self.PROPERTIES,
            }
        }
        if not self.ic.exists_type(index=self.index,
                                   doc_type=self.dbname):
            self.ic.put_mapping(index=self.index, doc_type=self.dbname,
                                body=self.mapping)
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
        merged_idents = {}
        for d in self.data:
            idents = d.get('identities', {})
            merged_idents.update(copy.copy(idents))

        self.idents = {}
        if self.default_data:
            self.idents = copy.copy(self.default_data.get('identities', {}))

        self.idents.update(merged_idents)

    def enrich(self):
        """ Here we convert provided date to epoch
        """
        for iid, id_data in self.idents.items():
            for email, email_data in id_data['emails'].items():
                for group, data in email_data.get('groups', {}).items():
                    if not data:
                        continue
                    for key in ('begin-date', 'end-date'):
                        if key in data:
                            data[key] = date2epoch(data[key])
                        else:
                            data[key] = None

    def validate(self):
        """ Validate self.data consistencies for identities
        """
        _, issues = self._check_basic('identities',
                                      idents_schema,
                                      'Identity')
        if issues:
            return issues
        for d in self.data:
            idents = d.get('identities', {})
            for iid, id_data in idents.items():
                if (id_data['default-email'] not in id_data['emails'].keys()):
                    issues.append("Identity %s default an unknown "
                                  "default-email" % iid)
                for email, email_data in id_data['emails'].items():
                    for group, data in email_data.get('groups', {}).items():
                        if not data:
                            continue
                        try:
                            for key in ('begin-date', 'end-date'):
                                if key in data:
                                    datetime.strptime(data[key], "%Y-%m-%d")
                        except Exception:
                            issues.append("Identity %s declares group %s "
                                          "membership invalid date %s" % (
                                              iid, group, data))
        return issues

    def load(self):
        self.delete_all()
        self.create_bulk(self.idents.items())

    def manage_bulk_err(self, exc):
        errs = [e['create']['error'] for e in exc[1]]
        if not all([True for e in errs if
                    e['type'] == 'document_already_exists_exception']):
            raise Exception(
                "Unable to create one or more doc: %s" % errs)

    def create_bulk(self, docs):
        def gen():
            for pid, doc in docs:
                d = {}
                d['_index'] = self.index
                d['_type'] = self.dbname
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
        def gen(docs):
            for doc in docs:
                d = {}
                d['_index'] = self.index
                d['_type'] = self.dbname
                d['_op_type'] = 'delete'
                d['_id'] = doc['_id']
                yield d
        bulk(self.es,
             gen(self.get_all(source=False)))
        self.es.indices.refresh(index=self.index)

    def get_all(self, source=True):
        query = {
            '_source': source,
            'query': {
                'match_all': {}
            }
        }
        return scanner(self.es, query=query, index=self.index,
                       doc_type=self.dbname)

    def create(self, user):
        self.es.create(self.index, self.dbname,
                       id=user['uid'],
                       body=user)
        self.es.indices.refresh(index=self.index)

    def update(self, user):
        self.es.update(self.index, self.dbname,
                       id=user['uid'],
                       body={'doc': user})
        self.es.indices.refresh(index=self.index)

    def get(self, uid, silent=True):
        try:
            res = self.es.get(index=self.index,
                              doc_type=self.dbname,
                              id=uid)
            return res['_source']
        except Exception as e:
            if silent:
                return None
            logger.error('Unable to get user (%s). %s' % (uid, e))

    def backend_convert_ident(self, ident):
        # Transform the data structure to be compatible
        data = {}
        data['name'] = ident['name']
        data['default-email'] = ident['default-email']
        data['emails'] = {}
        for email in ident['emails']:
            groups = {}
            data['emails'][email['email']] = {'groups': groups}
            if 'groups' in email.keys():
                for group in email['groups']:
                    groups[group['group']] = {}
                    for elm in ('begin-date', 'end-date'):
                        if elm in group.keys():
                            groups[group['group']][elm] = group[elm]
        return ident['uid'], data

    def _get_ident_by_id(self, id):
        return self.get(id)

    def get_ident_by_id(self, id):
        ident = self._get_ident_by_id(id)
        if ident:
            id, ident = self.backend_convert_ident(ident)
        if not ident:
            return id, None
        else:
            return id, ident

    def _get_idents_by_emails(self, emails):
        if not isinstance(emails, list):
            emails = (emails,)
        params = {'index': self.index, 'doc_type': self.dbname}
        body = {
            "query": {"filtered": {
                "filter": {"bool": {"must": {
                    "nested": {
                        "path": "emails",
                        "query": {
                            "bool": {
                                "should": [
                                    {"match": {"emails.email": email}} for
                                    email in emails
                                ]
                            }
                        }
                    }
                }}}
            }}
        }
        params['body'] = body
        # TODO(fbo): Improve by doing it by bulk instead
        params['size'] = 10000
        ret = self.es.search(**params)['hits']['hits']
        ret = [r['_source'] for r in ret]
        return ret

    def get_idents_by_emails(self, emails):
        if not isinstance(emails, list):
            emails = [emails]

        _selecteds = []
        if emails:
            # Do not request if emails is empty (EL will return
            # all ident in that case)
            el_selecteds = self._get_idents_by_emails(emails)
            emails_not_found = set(emails)
            for ident in el_selecteds:
                ident = self.backend_convert_ident(ident)
                _selecteds.append(ident)
                emails_not_found -= set(ident[1]['emails'].keys())
            for email in emails_not_found:
                _selecteds.append(
                    (email, {'name': None,
                                'default-email': email,
                                'emails': {email: {}}})
                    )

        selecteds = {}
        for uid, data in _selecteds:
            selecteds[uid] = data

        if len(emails) == 1 and len(selecteds) > 1:
            raise Exception("More than one idents matched the requested email")
        return selecteds

    def get_idents_in_group(self, group):
        params = {'index': self.index, 'doc_type': self.dbname}
        body = {
            "query": {"filtered": {
                "filter": {"bool": {"must": {
                    "nested": {
                        "path": "emails",
                        "query": {
                            "bool": {"must": {
                                "nested": {
                                    "path": "emails.groups",
                                    "query": {
                                        "bool": {"must": {
                                            "match": {
                                                "emails.groups.group": group}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }}}
            }}
        }
        params['body'] = body
        # TODO(fbo): Improve by doing it by bulk instead
        params['size'] = 10000
        ret = self.es.search(**params)['hits']['hits']
        return [r['_source'] for r in ret]

    def delete(self, uid):
        try:
            self.es.delete(self.index, self.dbname, uid)
            self.es.indices.refresh(index=self.index)
        except NotFoundError:
            pass
