import logging


class Projects(object):
    def __init__(self, connector=None):
        self.es = connector.es
        self.ic = connector.ic
        self.index = connector.index
        self.dbname = 'projects'
        self.mapping = {
            self.dbname: {
                "properties": {
                    "name": {"type": "string", "index": "not_analyzed"},
                    "projects": {
                        "properties": {
                            "uri": {"type": "string",
                                    "index": "not_analyzed"},
                            "branch": {"type": "string",
                                       "index": "not_analyzed"},
                        }
                    }
                }
            }
        }
        self.ic.put_mapping(index=self.index, doc_type=self.dbname,
                            body=self.mapping)

    def add_project(self, project):
        try:
            self.es.create(index=self.index,
                           doc_type=self.dbname,
                           id=project['name'],
                           body=project)
            self.es.indices.refresh(index=self.index)
        except Exception, e:
            logging.info('Unable to index project (%s). %s', (project, e))

    def get_project(self, name, source=True):
        try:
            return self.es.get(index=self.index,
                               doc_type=self.dbname,
                               id=name,
                               _source=source)
        except Exception, e:
            logging.info('Unable to get project (%s). %s', (name, e))
