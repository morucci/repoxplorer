# Copyright 2016, Fabien Boucher
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
from datetime import timedelta
from elasticsearch.helpers import scan as scanner
from elasticsearch.helpers import bulk

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
                    "line_modifieds": {"type": "integer",
                                       "index": "not_analyzed"},
                    "merge_commit": {"type": "boolean"},
                    "commit_msg": {"type": "string"}
                }
            }
        }
        self.ic.put_mapping(index=self.index, doc_type=self.dbname,
                            body=self.mapping)

    def add_commits(self, source_it):
        def gen(it):
            for source in it:
                d = {}
                d['_index'] = self.index
                d['_type'] = self.dbname
                d['_op_type'] = 'create'
                d['_id'] = source['sha']
                d['_source'] = source
                yield d
        bulk(self.es, gen(source_it))
        self.es.indices.refresh(index=self.index)

    def update_commits(self, source_it):
        """ Take the sha from each doc and use
        it to reference the doc id to delete then
        create the doc. The doc needs to be already updated.
        """
        def gen(it):
            for source in it:
                d = {}
                d['_index'] = self.index
                d['_type'] = self.dbname
                d['_op_type'] = 'delete'
                d['_id'] = source['sha']
                yield d
                d = {}
                d['_index'] = self.index
                d['_type'] = self.dbname
                d['_op_type'] = 'create'
                d['_id'] = source['sha']
                d['_source'] = source
                yield d
        bulk(self.es, gen(source_it))
        self.es.indices.refresh(index=self.index)

    def get_commit(self, sha):
        try:
            res = self.es.get(index=self.index,
                              doc_type=self.dbname,
                              id=sha)
            return res['_source']
        except Exception, e:
            logger.info('Unable to get commit (%s). %s' % (sha, e))

    def get_commits_by_id(self, sha_list):
        body = {"ids": sha_list}
        try:
            res = self.es.mget(index=self.index,
                               doc_type=self.dbname,
                               _source=True,
                               body=body)
            return res
        except Exception, e:
            logger.info('Unable to get mulitple commits. %s' % e)

    def del_commits(self, sha_list):
        def gen(it):
            for sha in it:
                d = {}
                d['_index'] = self.index
                d['_type'] = self.dbname
                d['_op_type'] = 'delete'
                d['_id'] = sha
                yield d
        bulk(self.es, gen(sha_list))
        self.es.indices.refresh(index=self.index)

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
                    sort='desc', scan=False, merge_commit=None):
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

        # If None both are return. If you expect to skip merge commits
        # then set merge_commit to False
        if merge_commit is not None:
            body["filter"]["bool"]["must"].append(
                {"term": {"merge_commit": merge_commit}})

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

    def get_line_modifieds_stats(self, mails=[], projects=[],
                                 fromdate=None, todate=None,
                                 merge_commit=None):
        """ Return the stats about line modifieds for authors and/or projects.
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
                "line_modifieds_stats": {
                    "stats": {
                        "field": "line_modifieds"
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

        if merge_commit is not None:
            body["query"]["filtered"]["filter"]["bool"]["must"].append(
                {"term": {"merge_commit": merge_commit}})

        params['body'] = body
        params['size'] = 0
        res = self.es.search(**params)
        took = res['took']
        return took, res["aggregations"]["line_modifieds_stats"]

    def get_top_authors(self, mails=[], projects=[],
                        fromdate=None, todate=None,
                        merge_commit=None):
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

        if merge_commit is not None:
            body["query"]["filtered"]["filter"]["bool"]["must"].append(
                {"term": {"merge_commit": merge_commit}})

        params['body'] = body
        params['size'] = 0
        res = self.es.search(**params)
        took = res['took']
        top = [(b['key'], (b['doc_count'],
                           b['top-author-hits']['hits']
                           ['hits'][0]['_source']['author_name']))
               for b in res["aggregations"]["top-author"]["buckets"]]
        return took, dict(top)

    def get_top_authors_by_lines(self, mails=[], projects=[],
                                 fromdate=None, todate=None,
                                 merge_commit=None):
        """ Return the ranking of author emails by modidified lines
        of codes
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
                "top-author-by-modified": {
                    "terms": {
                        "field": "author_email",
                        "size": 0,
                    },
                    "aggs": {
                        "modified": {
                            "sum": {
                                "field": "line_modifieds",
                            },
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

        if merge_commit is not None:
            body["query"]["filtered"]["filter"]["bool"]["must"].append(
                {"term": {"merge_commit": merge_commit}})

        params['body'] = body
        params['size'] = 0
        res = self.es.search(**params)
        took = res['took']
        top = [(b['key'], b['modified']['value'])
               for b in res["aggregations"]
               ["top-author-by-modified"]["buckets"]]
        return took, dict(top)

    def get_top_projects(self, mails=[], projects=[],
                         fromdate=None, todate=None,
                         merge_commit=None):
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

        if merge_commit is not None:
            body["query"]["filtered"]["filter"]["bool"]["must"].append(
                {"term": {"merge_commit": merge_commit}})

        params['body'] = body
        params['size'] = 0
        res = self.es.search(**params)
        took = res['took']
        top = [(b['key'], b['doc_count'])
               for b in res["aggregations"]["top-project"]["buckets"]]
        return took, dict(top)

    def get_commits_time_delta(self, mails=[], projects=[],
                               fromdate=None, todate=None,
                               merge_commit=None):
        first = self.get_commits(mails, projects, start=0, limit=1, sort='asc',
                                 fromdate=fromdate, todate=todate,
                                 merge_commit=merge_commit)
        first = first[2][0]['committer_date']
        last = self.get_commits(mails, projects, start=0, limit=1, sort='desc',
                                fromdate=fromdate, todate=todate,
                                merge_commit=merge_commit)
        last = last[2][0]['committer_date']
        duration = timedelta(seconds=last) - timedelta(seconds=first)
        duration = duration.total_seconds()
        return first, last, duration

    def get_commits_histo(self, mails=[], projects=[],
                          fromdate=None, todate=None,
                          merge_commit=None):
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
                        "field": "committer_date",
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

        if merge_commit is not None:
            body["query"]["filtered"]["filter"]["bool"]["must"].append(
                {"term": {"merge_commit": merge_commit}})

        params['body'] = body
        params['size'] = 0
        res = self.es.search(**params)
        took = res['took']
        return took, res["aggregations"]["commits"]["buckets"]
