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
import itertools

from collections import deque
from datetime import timedelta

from elasticsearch.helpers import scan as scanner
from elasticsearch.helpers import bulk

logger = logging.getLogger(__name__)

PROPERTIES = {
    "sha": {"type": "string", "index": "not_analyzed"},
    "author_date": {"type": "date", "format": "epoch_second"},
    "committer_date": {"type": "date", "format": "epoch_second"},
    "ttl": {"type": "integer", "index": "not_analyzed"},
    "author_name": {"type": "string"},
    "committer_name": {"type": "string"},
    "author_email": {"type": "string", "index": "not_analyzed"},
    "committer_email": {"type": "string", "index": "not_analyzed"},
    "repos": {"type": "string", "index": "not_analyzed"},
    "line_modifieds": {"type": "integer", "index": "not_analyzed"},
    "merge_commit": {"type": "boolean"},
    "commit_msg": {"type": "string"},
}

DYNAMIC_TEMPLATES = [
    {
        "strings": {
            "match": "*",
            "mapping": {
                "type": "string",
                "index": "not_analyzed",
            }
        }
    }
]


class Commits(object):
    def __init__(self, connector=None):
        self.es = connector.es
        self.ic = connector.ic
        self.index = connector.index
        self.dbname = 'commits'
        self.mapping = {
            self.dbname: {
                "properties": PROPERTIES,
                "dynamic_templates": DYNAMIC_TEMPLATES,
            }
        }
        if not self.ic.exists_type(index=self.index,
                                   doc_type=self.dbname):
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

    def update_commits(self, source_it, field='repos'):
        """ Take the sha from each doc and use
        it to reference the doc to update. This method only
        support updating a single field for now. The default one
        is repos because that's the only one to make sense in
        this context.
        """
        def gen(it):
            for source in it:
                d = {}
                d['_index'] = self.index
                d['_type'] = self.dbname
                d['_op_type'] = 'update'
                d['_id'] = source['sha']
                d['_source'] = {'doc': {field: source[field]}}
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
            logger.error('Unable to get commit (%s). %s' % (sha, e))

    def get_commits_by_id(self, sha_list):
        body = {"ids": sha_list}
        try:
            res = self.es.mget(index=self.index,
                               doc_type=self.dbname,
                               _source=True,
                               body=body)
            return res
        except Exception, e:
            logger.error('Unable to get mulitple commits. %s' % e)

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

    def get_filter(self, mails, repos, metadata):
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

        for repo in repos:
            should_repo_clause = {
                "bool": {
                    "must": []
                }
            }
            should_repo_clause["bool"]["must"].append(
                {"term": {"repos": repo}}
            )
            filter["bool"]["should"].append(should_repo_clause)

        must_metadata_clause = {
            "bool": {
                "should": []
            }
        }
        for key, value in metadata:
            if value is None:
                must_metadata_clause["bool"]["should"].append(
                    {"exists": {"field": key}}
                )
            else:
                must_metadata_clause["bool"]["should"].append(
                    {"term": {key: value}}
                )
        filter["bool"]["must"].append(must_metadata_clause)

        return filter

    def get_commits(self, mails=[], repos=[],
                    fromdate=None, todate=None, start=0, limit=100,
                    sort='desc', scan=False, merge_commit=None,
                    metadata=[]):
        """ Return the list of commits for authors and/or repos.
        """

        params = {'index': self.index, 'doc_type': self.dbname}

        if not mails and not repos and not metadata:
            raise Exception(
                'At least a author email or repo or a metadata'
                'is required to run a request')

        body = {
            "filter": self.get_filter(mails, repos, metadata),
        }

        # If None both are return. If you expect to skip merge commits
        # then set merge_commit to False
        if merge_commit is not None:
            body["filter"]["bool"]["must"].append(
                {"term": {"merge_commit": merge_commit}})

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

        if scan:
            return scanner(self.es, query=body,
                           index=self.index,
                           doc_type=self.dbname)

        params['body'] = body
        params['size'] = limit
        params['from_'] = start
        params['sort'] = "committer_date:%s,author_date:%s" % (sort, sort)
        res = self.es.search(**params)
        took = res['took']
        hits = res['hits']['total']
        commits = [r['_source'] for r in res['hits']['hits']]
        return took, hits, commits

    def get_commits_amount(self, mails=[], repos=[],
                           fromdate=None, todate=None,
                           merge_commit=None, metadata=[]):
        """ Return the amount of commits for authors and/or repos.
        """
        params = {'index': self.index, 'doc_type': self.dbname}

        if not mails and not repos:
            raise Exception('At least a author email or repo is required')

        body = {
            "query": {
                "filtered": {
                    "filter": self.get_filter(mails, repos, metadata),
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
        res = self.es.count(**params)
        return res['count']

    def get_line_modifieds_stats(self, **kwargs):
        return self.get_field_stats("line_modifieds", **kwargs)

    def get_ttl_stats(self, **kwargs):
        return self.get_field_stats("ttl", **kwargs)

    def get_field_stats(self, field, mails=[], repos=[],
                        fromdate=None, todate=None,
                        merge_commit=None, metadata=[]):
        """ Return the stats about the specified field for authors and/or repos.
        """
        params = {'index': self.index, 'doc_type': self.dbname}

        if not mails and not repos:
            raise Exception('At least a author email or repo is required')

        body = {
            "query": {
                "filtered": {
                    "filter": self.get_filter(mails, repos, metadata),
                }
            },
            "aggs": {
                "%s_stats" % field: {
                    "stats": {
                        "field": field
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
        return took, res["aggregations"]["%s_stats" % field]

    def get_authors(self, mails=[], repos=[],
                    fromdate=None, todate=None,
                    merge_commit=None, metadata=[]):
        """ Return the author emails (removed duplicated) also
        this return the amount of hits for a given unique
        author_email. The hits value is the amount of commits
        for a given email.
        """
        params = {'index': self.index, 'doc_type': self.dbname}

        body = {
            "query": {
                "filtered": {
                    "filter": self.get_filter(mails, repos, metadata),
                }
            },
            "aggs": {
                "authors": {
                    "terms": {
                        "field": "author_email",
                        "order": {"_count": "desc"},
                        "size": 0
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
        res = [(b['key'], b['doc_count'])
               for b in res["aggregations"]["authors"]["buckets"]]
        return took, dict(res)

    def get_commits_author_name_by_emails(self, mails=[]):
        """ Return the list author name based on the
        list of author email passed as a query. This fetchs
        each author name from the first commits found in the DB and
        uses the bulk search API to reduce round trip.
        """
        def subreq(mails):
            request = []
            for email in mails:
                req_head = {'index': self.index, 'type': self.dbname}
                req_body = {'query': {'term': {'author_email': email}},
                            'size': 1,
                            '_source': ["author_email", "author_name"]}
                request.extend([req_head, req_body])
            resp = self.es.msearch(body=request)
            return resp

        if not mails:
            raise Exception('At least an author email is required')

        ret = []
        resps = []
        amount = 100

        mails = deque(mails)
        while True:
            _mails = []
            for _ in xrange(amount):
                try:
                    _mails.append(mails.pop())
                except IndexError:
                    break
            if _mails:
                resps.append(subreq(_mails))
            else:
                break

        for resp in resps:
            for r in resp['responses']:
                try:
                    r['hits']['hits'][0]
                except Exception:
                    ret.append((None, None))
                    # Here we hit EsThreadPoolExecutor[search,
                    # queue capacity = 1000]
                    # print r
                    continue
                ret.append(
                    (r['hits']['hits'][0]['_source']['author_email'],
                     r['hits']['hits'][0]['_source']['author_name'])
                )
        return dict(ret)

    def get_top_authors_by_lines(self, **kwargs):
        return self.get_top_field_by_lines("author_email", **kwargs)

    def get_top_repos_by_lines(self, **kwargs):
        return self.get_top_field_by_lines("repos", **kwargs)

    def get_top_field_by_lines(self, field, mails=[], repos=[],
                               fromdate=None, todate=None,
                               merge_commit=None, metadata=[]):
        """ Return the ranking of author emails by modidified lines
        of codes
        """
        params = {'index': self.index, 'doc_type': self.dbname}

        if not mails and not repos:
            raise Exception('At least a author email or repo is required')

        body = {
            "query": {
                "filtered": {
                    "filter": self.get_filter(mails, repos, metadata),
                }
            },
            "aggs": {
                "top-field-by-modified": {
                    "terms": {
                        "field": field,
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
               ["top-field-by-modified"]["buckets"]]
        return took, dict(top)

    def get_metadata_keys(self, mails=[], repos=[],
                          fromdate=None, todate=None,
                          merge_commit=None):
        """ Return the metadata keys found inside
        the filtered commits. The returned dictionnary contains
        keys associated via the amount of hits.
        """
        uniq_keys = {}

        def storekey(key):
            if key not in uniq_keys:
                uniq_keys[key] = 1
            else:
                uniq_keys[key] += 1

        ret = self.get_commits(mails, repos,
                               fromdate, todate,
                               merge_commit=merge_commit, scan=True)
        keys = [c['_source'].keys() for c in ret]
        map(storekey, [i for i in itertools.chain(*keys) if
                       i not in PROPERTIES])
        return uniq_keys

    def get_metadata_key_values(self, key, mails=[], repos=[],
                                fromdate=None, todate=None,
                                merge_commit=None):
        """ Return for a metadata key the values found inside
        the filtered commits.
        """
        values = set()

        ret = self.get_commits(mails, repos,
                               fromdate, todate,
                               merge_commit=merge_commit,
                               metadata=((key, None),), scan=True)
        for c in ret:
            values |= set(c['_source'][key])
        values = list(values)
        values.sort()
        return values

    def get_repos(self, mails=[], repos=[],
                  fromdate=None, todate=None,
                  merge_commit=None, metadata={}):
        """ Return the repos (removed duplicated) also
        this return the amount of hits. The hits value is
        the amount of commit for an uniq repo.
        """
        params = {'index': self.index, 'doc_type': self.dbname}

        if not mails and not repos:
            raise Exception('At least a author email or repo is required')

        body = {
            "query": {
                "filtered": {
                    "filter": self.get_filter(mails, repos, metadata),
                }
            },
            "aggs": {
                "repos": {
                    "terms": {
                        "field": "repos",
                        "order": {"_count": "desc"},
                        "size": 0
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
               for b in res["aggregations"]["repos"]["buckets"]]
        return took, dict(top)

    def get_commits_time_delta(self, mails=[], repos=[],
                               fromdate=None, todate=None,
                               merge_commit=None, metadata=[]):
        first = self.get_commits(mails, repos, start=0, limit=1, sort='asc',
                                 fromdate=fromdate, todate=todate,
                                 merge_commit=merge_commit, metadata=metadata)
        first = first[2][0]['committer_date']
        last = self.get_commits(mails, repos, start=0, limit=1, sort='desc',
                                fromdate=fromdate, todate=todate,
                                merge_commit=merge_commit, metadata=metadata)
        last = last[2][0]['committer_date']
        duration = timedelta(seconds=last) - timedelta(seconds=first)
        duration = duration.total_seconds()
        return first, last, duration

    def get_commits_histo(self, mails=[], repos=[],
                          fromdate=None, todate=None,
                          merge_commit=None, metadata=[]):
        """ Return the histogram of contrib for authors and/or repos.
        """
        params = {'index': self.index, 'doc_type': self.dbname}

        if not mails and not repos:
            raise Exception('At least a author email or repo is required')

        qfilter = self.get_filter(mails, repos, metadata)
        duration = self.get_commits_time_delta(mails, repos,
                                               fromdate=fromdate,
                                               todate=todate,
                                               metadata=metadata)[2]

        # Set resolution by day if duration <= 3 months
        if (duration / (24 * 3600 * 31)) <= 3:
            res = 'day'
        # Set resolution by month if duration <= 10 years
        elif (duration / (24 * 3600 * 31 * 12)) <= 10:
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
