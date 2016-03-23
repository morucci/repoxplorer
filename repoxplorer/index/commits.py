import base64
import logging

logger = logging.getLogger(__name__)


class Commits(object):
    def __init__(self, connector=None):
        self.es = connector.es
        self.ic = connector.ic
        self.index = connector.index
        self.dbname = 'commits'
        self.mapping = {
            self.dbname: {
                "properties": {
                    "sha": {"type": "string", "index": "not_analyzed"},
                    "author_date": {"type": "integer",
                                    "index": "not_analyzed"},
                    "committer_date": {"type": "integer",
                                       "index": "not_analyzed"},
                    "author_name": {"type": "string"},
                    "committer_name": {"type": "string"},
                    "author_email": {"type": "string",
                                     "index": "not_analyzed"},
                    "committer_email": {"type": "string",
                                        "index": "not_analyzed"},
                    "project_branch": {"type": "string",
                                       "index": "not_analyzed"},
                    "project_uri": {"type": "string",
                                    "index": "not_analyzed"},
                    "project_name": {"type": "string",
                                     "index": "not_analyzed"},
                    "lines_modified": {"type": "integer",
                                       "index": "not_analyzed"},
                    "commit_msg": {"type": "string"}
                }
            }
        }
        self.ic.put_mapping(index=self.index, doc_type=self.dbname,
                            body=self.mapping)

    def uuid(self, project_uri, project_branch):
        return base64.b64encode('%s:%s' % (project_uri,
                                           project_branch))

    def add_commit(self, commit):
        cid = self.uuid(commit['project_uri'],
                        commit['project_branch'])
        try:
            self.es.create(index=self.index,
                           doc_type=self.dbname,
                           id=cid,
                           body=commit)
            self.es.indices.refresh(index=self.index)
        except Exception, e:
            logger.info('Unable to index commit (%s). %s' % (commit, e))

    def get_commit(self, cid, source=True):
        try:
            return self.es.get(index=self.index,
                               doc_type=self.dbname,
                               id=cid,
                               _source=source)
        except Exception, e:
            logger.info('Unable to get commit (%s). %s' % (cid, e))
