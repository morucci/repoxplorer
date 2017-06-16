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

logger = logging.getLogger(__name__)


class Users(object):

    PROPERTIES = {
        "uid": {"type": "string", "index": "not_analyzed"},
        "username": {"type": "string", "index": "not_analyzed"},
        "fullname": {"type": "string", "index": "not_analyzed"},
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

    def get(self, uid):
        try:
            res = self.es.get(index=self.index,
                              doc_type=self.dbname,
                              id=uid)
            return res['_source']
        except Exception, e:
            logger.error('Unable to get user (%s). %s' % (uid, e))

    def get_ident_by_id(self, id):
        return self.get(id)

    def get_ident_by_email(self, email):
        params = {'index': self.index, 'doc_type': self.dbname}
        body = {
            "query": {"filtered": {
                "filter": {"bool": {"must": {
                    "nested": {
                        "path": "emails",
                        "query": {
                            "bool": {"must": [{
                                "match": {"emails.email": email}}]
                            }
                        }
                    }
                }}}
            }}
        }
        params['body'] = body
        ret = self.es.search(**params)['hits']['hits']
        if len(ret) > 1:
            raise Exception("More than on user with an identical email")
        return ret[0]['_source']

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
                                                "emails.groups.group": group}}}
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
        ret = self.es.search(**params)['hits']['hits']
        return [r['_source'] for r in ret]

    def delete(self, uid):
        self.es.delete(self.index, self.dbname, uid)
        self.es.indices.refresh(index=self.index)


class Groups(object):

    PROPERTIES = {
        "gid": {"type": "string", "index": "not_analyzed"},
        "description": {"type": "string", "index": "not_analyzed"},
        "emails": {
            "type": "nested",
            "properties": {
                "email": {"type": "string", "index": "not_analyzed"},
                "begin-date": {"type": "string", "index": "not_analyzed"},
                "end-date": {"type": "string", "index": "not_analyzed"}
            },
        },
    }

    def __init__(self, connector=None):
        self.connector = connector
        self.es = connector.es
        self.ic = connector.ic
        self.index = connector.index
        self.dbname = 'groups'
        self.mapping = {
            self.dbname: {
                "properties": self.PROPERTIES,
            }
        }
        if not self.ic.exists_type(index=self.index,
                                   doc_type=self.dbname):
            self.ic.put_mapping(index=self.index, doc_type=self.dbname,
                                body=self.mapping)

    def create(self, group):
        self.es.create(self.index, self.dbname,
                       id=group['gid'],
                       body=group)
        self.es.indices.refresh(index=self.index)

    def update(self, group):
        self.es.update(self.index, self.dbname,
                       id=group['gid'],
                       body={'doc': group})
        self.es.indices.refresh(index=self.index)

    def _enrich(self, group, gid):
        # Find user mail part of that group
        users = Users(self.connector)
        idents = users.get_idents_in_group(gid)
        idents_emails = [ident['emails'] for ident in idents]
        for ident_emails in idents_emails:
            for ident_email in ident_emails:
                if 'groups' in ident_email.keys():
                    email = ident_email['email']
                    for _group in ident_email['groups']:
                        if _group['group'] == gid:
                            elem = {'email': email}
                            elem.update(_group)
                            del elem['group']
                            group['emails'].append(elem)
        return group

    def get(self, gid):
        try:
            res = self.es.get(index=self.index,
                              doc_type=self.dbname,
                              id=gid)
        except Exception, e:
            logger.error('Unable to get group (%s). %s' % (gid, e))
            return None
        # We look also to the users index to find group membership
        return self._enrich(res['_source'], gid)

    def get_all(self):
        params = {'index': self.index, 'doc_type': self.dbname}
        body = {"query": {'matchAll': {}}}
        params['body'] = body
        params['size'] = 10000
        return dict([(h['_id'], h['_source']) for h in
                     self.es.search(**params)['hits']['hits']])

    def get_group_by_id(self, id):
        return self.get(id)

    def delete(self, gid):
        self.es.delete(self.index, self.dbname, gid)
        self.es.indices.refresh(index=self.index)
