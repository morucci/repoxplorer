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

from elasticsearch.exceptions import NotFoundError

logger = logging.getLogger(__name__)


class Users(object):

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

    def __init__(self, connector=None):
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
        except Exception, e:
            if silent:
                return None
            logger.error('Unable to get user (%s). %s' % (uid, e))

    def get_ident_by_id(self, id):
        return self.get(id)

    def get_idents_by_emails(self, emails):
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
