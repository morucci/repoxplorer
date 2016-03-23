import logging


class Users(object):
    def __init__(self, connector=None):
        self.es = connector.es
        self.ic = connector.ic
        self.index = connector.index
        self.dbname = 'users'
        self.mapping = {
            self.dbname: {
                "properties": {
                    "login": {"type": "string", "index": "not_analyzed"},
                    "fullname": {"type": "string"},
                    "mails": {"type": "string", "index": "not_analyzed"}
                }
            }
        }
        self.ic.put_mapping(index=self.index, doc_type=self.dbname,
                            body=self.mapping)

    def add_user(self, user):
        try:
            self.es.create(index=self.index,
                           doc_type=self.dbname,
                           id=user['username'],
                           body=user)
            self.es.indices.refresh(index=self.index)
        except Exception, e:
            logging.info('Unable to index user (%s). %s', (user, e))

    def get_user(self, username, source=True):
        try:
            return self.es.get(index=self.index,
                               doc_type=self.dbname,
                               id=username,
                               _source=source)
        except Exception, e:
            logging.info('Unable to get user (%s). %s', (username, e))
