import logging
from datetime import timedelta
from elasticsearch import TransportError
from elasticsearch.helpers import scan as scanner

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
                    "author_date": {"type": "date",
                                    "format": "epoch_second"},
                    "committer_date": {"type": "date",
                                       "format": "epoch_second"},
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
            commit['projects'] = list(
                set(commit['projects']).union(set(orig['projects'])))
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
            # TODO need to be smarter to delete only if projects
            # become empty
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
                    fromdate=None, todate=None, start=0, limit=100,
                    sort='desc', scan=False):
        """ Return the list of commits for authors and/or projects.
        """

        params = {'index': self.index, 'doc_type': self.dbname}

        if not mails and not projects:
            raise Exception('At least a author email or project is required')

        body = {
            "filter": self.get_filter(mails, projects),
        }

        if scan:
            return scanner(self.es, query=body,
                           index=self.index,
                           doc_type=self.dbname)

        body["filter"]["bool"]["must"].append(
            {
                "range": {
                    "committer_date": {
                        "gte": fromdate,
                        "lt": todate,
                    }
                }
            }
        )

        params['body'] = body
        params['size'] = limit
        params['from_'] = start
        params['sort'] = "committer_date:%s,author_date:%s" % (sort, sort)
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
            }
        }

        body["query"]["filtered"]["filter"]["bool"]["must"].append(
            {
                "range": {
                    "committer_date": {
                        "gte": fromdate,
                        "lt": todate,
                    }
                }
            }
        )

        params['body'] = body
        res = self.es.count(**params)
        return res['count']

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
                    "committer_date": {
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

    def get_top_authors(self, mails=[], projects=[],
                        fromdate=None, todate=None):
        """ Return the ranking of author emails
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
                "top-author": {
                    "terms": {
                        "field": "author_email",
                        "size": 0
                    },
                    "aggs": {
                        "top-author-hits": {
                            "top_hits": {
                                "sort": [
                                    {
                                        "committer_date": {
                                            "order": "desc"
                                        }
                                    }],
                                "_source": {
                                    "include": [
                                        "author_name",
                                    ]
                                },
                                "size": 1
                            }
                        }
                    }
                }
            }
        }

        body["query"]["filtered"]["filter"]["bool"]["must"].append(
            {
                "range": {
                    "committer_date": {
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
        top = [(b['key'], (b['doc_count'],
                           b['top-author-hits']['hits']
                           ['hits'][0]['_source']['author_name']))
               for b in res["aggregations"]["top-author"]["buckets"]]
        return took, dict(top)

    def get_top_projects(self, mails=[], projects=[],
                         fromdate=None, todate=None):
        """ Return the ranking of project contributed
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
                "top-project": {
                    "terms": {
                        "field": "projects",
                        "size": 50
                    },
                    "aggs": {
                        "top-projects-hits": {
                            "top_hits": {
                                "sort": [
                                    {
                                        "committer_date": {
                                            "order": "desc"
                                        }
                                    }],
                                "size": 1
                            }
                        }
                    }
                }
            }
        }

        body["query"]["filtered"]["filter"]["bool"]["must"].append(
            {
                "range": {
                    "committer_date": {
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
        top = [(b['key'], b['doc_count'])
               for b in res["aggregations"]["top-project"]["buckets"]]
        return took, dict(top)

    def get_commits_time_delta(self, mails=[], projects=[],
                               fromdate=None, todate=None):
        first = self.get_commits(mails, projects, start=0, limit=1, sort='asc',
                                 fromdate=fromdate, todate=todate)
        first = first[2][0]['committer_date']
        last = self.get_commits(mails, projects, start=0, limit=1, sort='desc',
                                fromdate=fromdate, todate=todate)
        last = last[2][0]['committer_date']
        duration = timedelta(seconds=last) - timedelta(seconds=first)
        duration = duration.total_seconds()
        return first, last, duration

    def get_commits_histo(self, mails=[], projects=[],
                          fromdate=None, todate=None):
        """ Return the histogram of contrib for authors and/or projects.
        """
        params = {'index': self.index, 'doc_type': self.dbname}

        if not mails and not projects:
            raise Exception('At least a author email or project is required')

        qfilter = self.get_filter(mails, projects)
        duration = self.get_commits_time_delta(mails, projects,
                                               fromdate=fromdate,
                                               todate=todate)[2]

        # Set resolution by day if duration <= 2 months
        if (duration / (24 * 3600 * 31)) <= 2:
            res = 'day'
        # Set resolution by month if duration <= 3 years
        elif (duration / (24 * 3600 * 31 * 12)) <= 3:
            res = 'month'
        else:
            res = 'year'

        body = {
            "query": {
                "filtered": {
                    "filter": qfilter,
                }
            },
            "aggs": {
                "commits": {
                    "date_histogram": {
                        "field": "author_date",
                        "interval": res,
                        "format": "yyyy-MM-dd",
                    }
                }
            }
        }

        body["query"]["filtered"]["filter"]["bool"]["must"].append(
            {
                "range": {
                    "committer_date": {
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
        return took, res["aggregations"]["commits"]["buckets"]
