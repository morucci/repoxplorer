import logging
from elasticsearch import TransportError

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
                    "projects": {"type": "string",
                                 "index": "not_analyzed"},
                    "lines_modified": {"type": "integer",
                                       "index": "not_analyzed"},
                    "commit_msg": {"type": "string"}
                }
            }
        }
        self.ic.put_mapping(index=self.index, doc_type=self.dbname,
                            body=self.mapping)

    def add_commit(self, commit):
        if 'projects' not in commit:
            commit['projects'] = [commit['project'], ]
        if 'project' in commit.keys():
            del commit['project']
        try:
            self.es.create(index=self.index,
                           doc_type=self.dbname,
                           id=commit['sha'],
                           body=commit)
            self.es.indices.refresh(index=self.index)
        except TransportError, e:
            if e.status_code == 409:
                self.update_commit(commit['sha'], commit)
        except Exception, e:
            logger.info('Unable to index commit (%s). %s' % (commit, e))

    def update_commit(self, sha, commit):
        """ This is used only when we need to tag a commit
        in another project or branch.
        """
        try:
            orig = self.get_commit(commit['sha'])
            commit['projects'].extend(orig['projects'])
            self.del_commit(sha)
            self.add_commit(commit)
        except Exception, e:
            logger.info('Unable to update commit (%s). %s' % (commit, e))

    def get_commit(self, sha):
        try:
            res = self.es.get(index=self.index,
                              doc_type=self.dbname,
                              id=sha)
            return res['_source']
        except Exception, e:
            logger.info('Unable to get commit (%s). %s' % (sha, e))

    def del_commit(self, sha):
        try:
            self.es.delete(index=self.index,
                           doc_type=self.dbname,
                           id=sha)
            self.es.indices.refresh(index=self.index)
        except Exception, e:
            logger.info('Unable to del commit (%s). %s' % (sha, e))

    def get_filter(self, mails, projects):
        """ Compute the search filter
        """
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
            should_project_clause["bool"]["must"].append(
                {"term": {"projects": project}}
            )
            filter["bool"]["should"].append(should_project_clause)

        return filter

    def get_commits(self, mails=[], projects=[],
                    fromdate=None, todate=None, start=0, limit=100):
        """ Return the list of commits for authors and/or projects.
        """

        params = {'index': self.index, 'doc_type': self.dbname}

        if not mails and not projects:
            raise Exception('At least a author email or project is required')

        body = {
            "filter": self.get_filter(mails, projects),
        }

        body["filter"]["bool"]["must"].append(
            {
                "range": {
                    "author_date": {
                        "gte": fromdate,
                        "lt": todate,
                    }
                }
            }
        )

        params['body'] = body
        params['size'] = limit
        params['from_'] = start
        params['sort'] = "committer_date:desc,author_date:desc"
        res = self.es.search(**params)
        took = res['took']
        hits = res['hits']['total']
        commits = [r['_source'] for r in res['hits']['hits']]
        return took, hits, commits

    def get_commits_amount(self, mails=[], projects=[],
                           fromdate=None, todate=None):
        """ Return the amount of commits for authors and/or projects.
        """
        params = {'index': self.index, 'doc_type': self.dbname}

        if not mails and not projects:
            raise Exception('At least a author email or project is required')

        body = {
            "query": {
                "filtered": {
                    "filter": self.get_filter(mails, projects),
                }
            },
            "aggs": {
                "commits_count": {
                    # Make sure we count unique value of sha
                    # The same sha can appears on mulitple branches
                    # or project forks
                    "cardinality": {
                        "field": "sha"
                     }
                 }
            }
        }

        body["query"]["filtered"]["filter"]["bool"]["must"].append(
            {
                "range": {
                    "author_date": {
                        "gte": fromdate,
                        "lt": todate,
                    }
                }
            }
        )

        params['body'] = body
        params['size'] = 0
        res = self.es.search(**params)
        took = res['took']
        return took, res["aggregations"]["commits_count"]["value"]

    def get_lines_modified_stats(self, mails=[], projects=[],
                                 fromdate=None, todate=None):
        """ Return the stats about lines modified for authors and/or projects.
        """
        params = {'index': self.index, 'doc_type': self.dbname}

        if not mails and not projects:
            raise Exception('At least a author email or project is required')

        body = {
            "query": {
                "filtered": {
                    "filter": self.get_filter(mails, projects),
                }
            },
            "aggs": {
                "lines_modified_stats": {
                   "stats": {
                       "field": "lines_modified"
                    }
                }
            }
        }

        body["query"]["filtered"]["filter"]["bool"]["must"].append(
            {
                "range": {
                    "author_date": {
                        "gte": fromdate,
                        "lt": todate,
                    }
                }
            }
        )

        params['body'] = body
        params['size'] = 0
        res = self.es.search(**params)
        took = res['took']
        return took, res["aggregations"]["lines_modified_stats"]

    def get_top_author(self, mails=[], projects=[],
                       fromdate=None, todate=None):
        """ Return the ranking of author emails
        """
        pass

    def get_author_projects(self, mails=[], projects=[],
                            fromdate=None, todate=None):
        """ Return the list of projects for authors sort
        by commit amount and lines modified amount
        """
        pass
