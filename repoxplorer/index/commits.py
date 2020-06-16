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
from repoxplorer.index import add_params
from repoxplorer.index import clean_empty
from repoxplorer.index import get_elasticsearch_version

logger = logging.getLogger(__name__)

PROPERTIES = {
    "sha": {"type": "keyword"},
    "author_date": {"type": "date", "format": "epoch_second"},
    "committer_date": {"type": "date", "format": "epoch_second"},
    "ttl": {"type": "integer"},
    "author_name": {"type": "text"},
    "committer_name": {"type": "text"},
    "author_email": {"type": "keyword"},
    "author_email_domain": {"type": "keyword"},
    "committer_email": {"type": "keyword"},
    "repos": {"type": "keyword"},
    "line_modifieds": {"type": "integer"},
    "merge_commit": {"type": "boolean"},
    "commit_msg": {"type": "text"},
    "files_list": {"type": "keyword"},
}

DYNAMIC_TEMPLATES = [
    {
        "strings": {
            "match": "*",
            "mapping": {
                "type": "keyword",
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
            kwargs = add_params(self.es)
            self.ic.put_mapping(index=self.index, doc_type=self.dbname,
                                body=self.mapping, **kwargs)

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

    def get_commit(self, sha, silent=False):
        try:
            if get_elasticsearch_version(self.es) >= 7:
                res = self.es.get(index=self.index,
                                  id=sha)
            else:
                res = self.es.get(index=self.index,
                                  doc_type=self.dbname,
                                  id=sha)
            return res['_source']
        except Exception as e:
            if silent:
                return None
            logger.error('Unable to get commit (%s). %s' % (sha, e))

    def get_commits_by_id(self, sha_list):
        body = {"ids": sha_list}
        try:
            if get_elasticsearch_version(self.es) >= 7:
                res = self.es.mget(index=self.index,
                                   _source=True,
                                   body=body)
            else:
                res = self.es.mget(index=self.index,
                                   doc_type=self.dbname,
                                   _source=True,
                                   body=body)
            return res
        except Exception as e:
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

    def get_filter(self, mails, repos, metadata,
                   mails_neg=False, domains=None, blacklisted_mails=None):
        """ Compute the search filter
        """
        if isinstance(mails, list):
            mails = dict([(mail, None) for mail in mails])
        if isinstance(repos, list):
            repos = dict([(repo, None) for repo in repos])
        if not domains:
            domains = []

        filter = {
            "bool": {
                "must": [],
                "must_not": [],
                }
            }

        must_mail_clause = {
            "bool": {
                "should": [],
                "must_not": []
            }
        }

        for mail, date_bounces in mails.items():
            must = {"bool": {"must": []}}
            must["bool"]["must"].append({"term": {"author_email": mail}})
            if date_bounces:
                date_clause = {
                    "range": {
                        "committer_date": {
                            "gte": date_bounces.get('begin-date'),
                            "lt": date_bounces.get('end-date')
                        }
                    }
                }
                must["bool"]["must"].append(date_clause)
            if mails_neg:
                must_mail_clause["bool"]["must_not"].append(must)
            else:
                must_mail_clause["bool"]["should"].append(must)

        for domain in domains:
            clause = {"bool": {"must": []}}
            clause["bool"]["must"].append(
                {"term": {"author_email_domain": domain}})
            if mails_neg:
                must_mail_clause["bool"]["must_not"].append(clause)
            else:
                must_mail_clause["bool"]["should"].append(clause)

        filter["bool"]["must"].append(must_mail_clause)

        must_project_clause = {
            "bool": {
                "should": []
            }
        }
        for repo, paths in repos.items():
            repo_clause = {"bool": {"must": []}}
            repo_clause["bool"]["must"].append(
                {"bool": {
                    "must": [{"term": {"repos": repo}}],
                    "should": [],
                    "filter": [],
                }}
            )
            if paths:
                repo_clause["bool"]["must"][0]["bool"]["filter"].append(
                        {"terms": {"files_list": []}}
                )
                for path in paths:
                    repo_clause["bool"]["must"][0]["bool"]["filter"][0][
                        "terms"]["files_list"].append(path)

            must_project_clause["bool"]["should"].append(repo_clause)

        filter["bool"]["must"].append(must_project_clause)

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

        # Exclude commits from 1970-01-01
        boggus_date_clause = {
            "range": {
                "committer_date": {
                    "gte": 86401,
                }
            }
        }
        filter["bool"]["must"].append(boggus_date_clause)

        if blacklisted_mails:
            for mail in blacklisted_mails:
                filter["bool"]["must_not"].append(
                    {"term": {"author_email": mail}})

        return clean_empty(filter)

    def get_commits(self, mails=[], repos=[],
                    fromdate=None, todate=None, start=0, limit=100,
                    sort='desc', scan=False, merge_commit=None,
                    metadata=[], mails_neg=False, domains=None,
                    blacklisted_mails=None):
        """ Return the list of commits for authors and/or repos.
        """

        params = {'index': self.index, 'doc_type': self.dbname}

        qfilter = self.get_filter(
            mails, repos, metadata,
            mails_neg, domains, blacklisted_mails)

        # If None both are returned. If you expect to skip merge commits
        # then set merge_commit to False
        if merge_commit is not None:
            qfilter["bool"]["must"].append(
                {"term": {"merge_commit": merge_commit}}
            )

        qfilter["bool"]["must"].append(
            {
                "range": {
                    "committer_date": {
                        "gte": fromdate,
                        "lt": todate,
                    }
                }
            }
        )

        body = {
            "query": {
                "bool": {
                    "filter": qfilter,
                }
            }
        }

        if scan:
            if get_elasticsearch_version(self.es) >= 7:
                return scanner(self.es, query=body,
                               index=self.index)
            else:
                return scanner(self.es, query=body,
                               index=self.index,
                               doc_type=self.dbname)

        params['body'] = body
        params['size'] = limit
        params['from_'] = start
        params['sort'] = "committer_date:%s,author_date:%s" % (sort, sort)
        params = clean_empty(params)
        if get_elasticsearch_version(self.es) >= 7:
            params.pop('doc_type')
        res = self.es.search(**params)
        took = res['took']
        hits = res['hits']['total']
        if isinstance(hits, dict) and 'value' in hits:
            hits = hits.get('value')
        commits = [r['_source'] for r in res['hits']['hits']]
        return took, hits, commits

    def get_commits_amount(self, mails=[], repos=[],
                           fromdate=None, todate=None,
                           merge_commit=None, metadata=[],
                           mails_neg=False, domains=None,
                           blacklisted_mails=None):
        """ Return the amount of commits for authors and/or repos.
        """
        params = {'index': self.index, 'doc_type': self.dbname}

        body = {
            "query": {
                "bool": {
                    "filter": self.get_filter(
                        mails, repos, metadata, mails_neg, domains,
                        blacklisted_mails),
                }
            }
        }

        body["query"]["bool"]["filter"]["bool"]["must"].append(
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
            body["query"]["bool"]["filter"]["bool"]["must"].append(
                {"term": {"merge_commit": merge_commit}})

        params['body'] = body
        params = clean_empty(params)
        if get_elasticsearch_version(self.es) >= 7:
            params.pop('doc_type')
        res = self.es.count(**params)
        return res['count']

    def get_line_modifieds_stats(self, **kwargs):
        return self.get_field_stats("line_modifieds", **kwargs)

    def get_ttl_stats(self, **kwargs):
        return self.get_field_stats("ttl", **kwargs)

    def get_field_stats(self, field, mails=[], repos=[],
                        fromdate=None, todate=None,
                        merge_commit=None, metadata=[],
                        mails_neg=False, domains=None, blacklisted_mails=None):
        """ Return the stats about the specified field for authors and/or repos.
        """
        params = {'index': self.index, 'doc_type': self.dbname}

        body = {
            "query": {
                "bool": {
                    "filter": self.get_filter(
                        mails, repos, metadata, mails_neg, domains,
                        blacklisted_mails),
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

        body["query"]["bool"]["filter"]["bool"]["must"].append(
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
            body["query"]["bool"]["filter"]["bool"]["must"].append(
                {"term": {"merge_commit": merge_commit}})

        params['body'] = body
        params['size'] = 0
        params = clean_empty(params)
        if get_elasticsearch_version(self.es) >= 7:
            params.pop('doc_type')
        res = self.es.search(**params)
        took = res['took']
        return took, res["aggregations"]["%s_stats" % field]

    def get_authors(self, mails=[], repos=[],
                    fromdate=None, todate=None,
                    merge_commit=None, metadata=[],
                    mails_neg=False, domains=None, blacklisted_mails=None):
        """ Return the author emails (removed duplicated) also
        this return the amount of hits for a given unique
        author_email. The hits value is the amount of commits
        for a given email.
        """
        params = {'index': self.index, 'doc_type': self.dbname}

        body = {
            "query": {
                "bool": {
                    "filter": self.get_filter(
                        mails, repos, metadata, mails_neg, domains,
                        blacklisted_mails),
                }
            },
            "aggs": {
                "authors": {
                    "terms": {
                        "field": "author_email",
                        "order": {"_count": "desc"},
                        "size": 1000000
                    }
                }
            }
        }

        body["query"]["bool"]["filter"]["bool"]["must"].append(
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
            body["query"]["bool"]["filter"]["bool"]["must"].append(
                {"term": {"merge_commit": merge_commit}})

        params['body'] = body
        params['size'] = 0
        params = clean_empty(params)
        if get_elasticsearch_version(self.es) >= 7:
            params.pop('doc_type')
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
            request = clean_empty(request)
            resp = self.es.msearch(body=request)
            return resp

        ret = []
        resps = []
        amount = 100

        mails = deque(mails)
        while True:
            _mails = []
            for _ in range(amount):
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
                               merge_commit=None, metadata=[],
                               mails_neg=False, domains=None,
                               blacklisted_mails=None):
        """ Return the ranking of field by lines changed
        """
        params = {'index': self.index, 'doc_type': self.dbname}

        body = {
            "query": {
                "bool": {
                    "filter": self.get_filter(
                        mails, repos, metadata, mails_neg, domains,
                        blacklisted_mails),
                }
            },
            "aggs": {
                "top-field-by-modified": {
                    "terms": {
                        "field": field,
                        "size": 1000000,
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

        body["query"]["bool"]["filter"]["bool"]["must"].append(
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
            body["query"]["bool"]["filter"]["bool"]["must"].append(
                {"term": {"merge_commit": merge_commit}})

        params['body'] = body
        params['size'] = 0
        params = clean_empty(params)
        if get_elasticsearch_version(self.es) >= 7:
            params.pop('doc_type')
        res = self.es.search(**params)
        took = res['took']
        top = [(b['key'], b['modified']['value'])
               for b in res["aggregations"]
               ["top-field-by-modified"]["buckets"]]
        return took, dict(top)

    def get_metadata_keys(self, mails=[], repos=[],
                          fromdate=None, todate=None,
                          merge_commit=None, mails_neg=False,
                          domains=None, blacklisted_mails=None):
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
        # Query the last 10000 commits to find metadata keys
        # This is not search accross the full set of commits
        # because the goal is to find most used metadata keys so
        # doing it on a limited set of commits is fine. And also
        # it lets the endpoint return data far faster.
        ret = self.get_commits(mails, repos, fromdate, todate,
                               merge_commit=merge_commit,
                               mails_neg=mails_neg, domains=domains,
                               blacklisted_mails=blacklisted_mails,
                               limit=10000)
        keys = [list(c.keys()) for c in ret[2]]
        list(map(storekey, [i for i in itertools.chain(*keys) if
                            i not in PROPERTIES]))
        return uniq_keys

    def get_metadata_key_values(self, key, mails=[], repos=[],
                                fromdate=None, todate=None,
                                merge_commit=None, mails_neg=False,
                                domains=None, blacklisted_mails=None):
        """ Return for a metadata key the values found inside
        the filtered commits.
        """
        values = set()

        ret = self.get_commits(mails, repos,
                               fromdate, todate,
                               merge_commit=merge_commit,
                               metadata=((key, None),), scan=True,
                               mails_neg=mails_neg,
                               domains=domains,
                               blacklisted_mails=blacklisted_mails)
        for c in ret:
            values |= set(c['_source'][key])
        values = list(values)
        values.sort()
        return values

    def get_repos(self, mails=[], repos=[],
                  fromdate=None, todate=None,
                  merge_commit=None, metadata={},
                  mails_neg=False, domains=None, blacklisted_mails=None):
        """ Return the repos (removed duplicated) also
        this return the amount of hits. The hits value is
        the amount of commit for an uniq repo.
        """
        params = {'index': self.index, 'doc_type': self.dbname}

        body = {
            "query": {
                "bool": {
                    "filter": self.get_filter(
                        mails, repos, metadata, mails_neg, domains,
                        blacklisted_mails),
                }
            },
            "aggs": {
                "repos": {
                    "terms": {
                        "field": "repos",
                        "order": {"_count": "desc"},
                        "size": 1000000
                    }
                }
            }
        }

        body["query"]["bool"]["filter"]["bool"]["must"].append(
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
            body["query"]["bool"]["filter"]["bool"]["must"].append(
                {"term": {"merge_commit": merge_commit}})

        params['body'] = body
        params['size'] = 0
        params = clean_empty(params)
        if get_elasticsearch_version(self.es) >= 7:
            params.pop('doc_type')
        res = self.es.search(**params)
        took = res['took']
        top = [(b['key'], b['doc_count'])
               for b in res["aggregations"]["repos"]["buckets"]]
        return took, dict(top)

    def get_commits_time_delta(self, mails=[], repos=[],
                               fromdate=None, todate=None,
                               merge_commit=None, metadata=[],
                               mails_neg=False, domains=None,
                               blacklisted_mails=None):
        first = self.get_commits(mails, repos, start=0, limit=1, sort='asc',
                                 fromdate=fromdate, todate=todate,
                                 merge_commit=merge_commit, metadata=metadata,
                                 mails_neg=mails_neg, domains=domains,
                                 blacklisted_mails=blacklisted_mails)
        first = first[2][0]['committer_date']
        last = self.get_commits(mails, repos, start=0, limit=1, sort='desc',
                                fromdate=fromdate, todate=todate,
                                merge_commit=merge_commit, metadata=metadata,
                                mails_neg=mails_neg, domains=domains,
                                blacklisted_mails=blacklisted_mails)
        last = last[2][0]['committer_date']
        duration = timedelta(seconds=last) - timedelta(seconds=first)
        duration = int(duration.total_seconds())
        return first, last, duration

    def set_histo_granularity(self, duration):
        # Set resolution by day if duration <= 3 months
        if (duration / (24 * 3600 * 31)) <= 3:
            res = 'day'
        # Set resolution by month if duration <= 10 years
        elif (duration / (24 * 3600 * 31 * 12)) <= 10:
            res = 'month'
        else:
            res = 'year'
        return res

    def get_commits_histo(self, mails=[], repos=[],
                          fromdate=None, todate=None,
                          merge_commit=None, metadata=[],
                          mails_neg=False, domains=None,
                          blacklisted_mails=None):
        """ Return the histogram of contrib for authors and/or repos.
        """
        params = {'index': self.index, 'doc_type': self.dbname}

        qfilter = self.get_filter(
            mails, repos, metadata, mails_neg, domains,
            blacklisted_mails)
        duration = self.get_commits_time_delta(
            mails, repos, fromdate=fromdate, todate=todate,
            metadata=metadata, mails_neg=mails_neg, domains=domains,
            blacklisted_mails=blacklisted_mails)[2]

        res = self.set_histo_granularity(duration)

        body = {
            "query": {
                "bool": {
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

        body["query"]["bool"]["filter"]["bool"]["must"].append(
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
            body["query"]["bool"]["filter"]["bool"]["must"].append(
                {"term": {"merge_commit": merge_commit}})

        params['body'] = body
        params['size'] = 0
        params = clean_empty(params)
        if get_elasticsearch_version(self.es) >= 7:
            params.pop('doc_type')
        res = self.es.search(**params)
        took = res['took']
        return took, res["aggregations"]["commits"]["buckets"]

    def get_authors_histo(self, mails=[], repos=[],
                          fromdate=None, todate=None,
                          merge_commit=None, metadata=[],
                          mails_neg=False, domains=None,
                          blacklisted_mails=None):
        """ Return the histogram of authors for authors and/or repos.
        """
        params = {'index': self.index, 'doc_type': self.dbname}

        qfilter = self.get_filter(
            mails, repos, metadata, mails_neg, domains,
            blacklisted_mails)
        duration = self.get_commits_time_delta(
            mails, repos, fromdate=fromdate, todate=todate,
            metadata=metadata, mails_neg=mails_neg,
            domains=domains, blacklisted_mails=blacklisted_mails)[2]

        res = self.set_histo_granularity(duration)

        body = {
            "query": {
                "bool": {
                    "filter": qfilter,
                }
            },
            "aggs": {
                "commits": {
                    "date_histogram": {
                        "field": "committer_date",
                        "interval": res,
                        "format": "yyyy-MM-dd",
                    },
                    "aggs": {
                        "authors_email": {
                            "terms": {
                                "field": "author_email",
                                "size": 1000000
                            },
                        }
                    }
                }
            }
        }

        body["query"]["bool"]["filter"]["bool"]["must"].append(
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
            body["query"]["bool"]["filter"]["bool"]["must"].append(
                {"term": {"merge_commit": merge_commit}})

        params['body'] = body
        params['size'] = 0
        params = clean_empty(params)
        if get_elasticsearch_version(self.es) >= 7:
            params.pop('doc_type')
        res = self.es.search(**params)
        took = res['took']
        res = res["aggregations"]["commits"]["buckets"]
        for bucket in res:
            bucket['authors_email'] = [
                b['key'] for b in bucket['authors_email']['buckets']]
            bucket['doc_count'] = len(bucket['authors_email'])
        return took, res
