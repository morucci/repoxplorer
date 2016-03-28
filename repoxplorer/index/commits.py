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
                    "author_date": {"type": "date"},
                    "committer_date": {"type": "date"},
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

    def uuid(self, project_uri, project_branch, sha):
        return base64.b64encode('%s:%s:%s' % (project_uri,
                                              project_branch,
                                              sha))

    def add_commit(self, commit):
        cid = self.uuid(commit['project_uri'],
                        commit['project_branch'],
                        commit['sha'])
        try:
            self.es.create(index=self.index,
                           doc_type=self.dbname,
                           id=cid,
                           body=commit)
            self.es.indices.refresh(index=self.index)
        except Exception, e:
            logger.info('Unable to index commit (%s). %s' % (commit, e))

    def get_commit(self, cid):
        try:
            res = self.es.get(index=self.index,
                              doc_type=self.dbname,
                              id=cid)
            return res['_source']
        except Exception, e:
            logger.info('Unable to get commit (%s). %s' % (cid, e))

    def get_commits(self, **kargs):
        search_keys = ('author_email',
                       'project_branch',
                       'project_uri',
                       'project_name')
        search_options = ('fromdate',
                          'todate',
                          'start',
                          'limit')
        for key in kargs:
            assert key in search_keys + search_options

        params = {'index': self.index, 'doc_type': self.dbname}

        body = {
            "filter": {
                "bool": {
                    "must": []
                }
            }
        }

        for key, value in kargs.items():
            if key not in search_keys:
                continue
            if value is None:
                continue
            body["filter"]["bool"]["must"].append(
                {"term": {key: value}}
            )

        if 'fromdate' in kargs and 'todate' in kargs:
            body["filter"]["bool"]["must"].append(
                {
                    "range": {
                        "author_date": {
                            "gte": kargs['fromdate'],
                            "lt": kargs['todate'],
                        }
                    }
                }
            )

        params['body'] = body
        params['size'] = kargs.get('limit', 100)
        params['from_'] = kargs.get('start', 0)
        params['sort'] = "committer_date:desc,author_date:desc"
        res = self.es.search(**params)
        took = res['took']
        hits = res['hits']['total']
        commits = [r['_source'] for r in res['hits']['hits']]
        return took, hits, commits

    # TODO: mails should be able to be empty and then rename method !
    def get_commits_amount_by_author(self, mails, projects=[]):
        """ Return the amount of commits for a contributor
        This allows to return the total amount of commits
        inside the index or in a set of projects. A author can
        be indentified by a set of mails
        """
        params = {'index': self.index, 'doc_type': self.dbname}

        filter = {
            "bool": {
                "must": [],
                "should": [],
                }
            }

        must_mail_clause = {
            "bool": {
                "should": []
            }
        }
        for mail in mails:
            must_mail_clause["bool"]["should"].append(
                    {"term": {"author_email": mail}}
            )
        filter["bool"]["must"].append(must_mail_clause)

        for project in projects:
            should_project_clause = {
                "bool": {
                    "must": []
                }
            }
            for key, value in project.items():
                should_project_clause["bool"]["must"].append(
                    {"term": {key: value}}
                )
            filter["bool"]["should"].append(should_project_clause)

        body = {
            "query": {
                "filtered": {
                    "filter": filter,
                }
            },
            "aggs": {
                "commits_count": {
                    "cardinality": {
                        "field": "sha"
                     }
                 }
            }
        }
        params['body'] = body
        params['size'] = 0
        res = self.es.search(**params)
        took = res['took']
        return took, res["aggregations"]["commits_count"]["value"]
