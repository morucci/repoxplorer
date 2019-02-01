# Copyright 2017, Fabien Boucher
# Copyright 2017, Red Hat
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

import hashlib
from collections import OrderedDict

from pecan import expose

from pecan import conf
from repoxplorer import index
from repoxplorer.controllers import utils
from repoxplorer.index.commits import Commits
from repoxplorer.index.contributors import Contributors

xorkey = conf.get('xorkey') or 'default'


class SearchController(object):

    @expose('json')
    def search_authors(self, query=""):
        ret_limit = 100
        c = Commits(index.Connector())
        ret = c.es.search(
            index=c.index, doc_type=c.dbname,
            q=query, df="author_name", size=10000,
            default_operator="AND",
            _source_include=["author_name", "author_email"])
        ret = ret['hits']['hits']
        if not len(ret):
            return {}
        idents = Contributors()
        authors = dict([(d['_source']['author_email'],
                         d['_source']['author_name']) for d in ret])
        result = {}
        _idents = idents.get_idents_by_emails(list(authors.keys())[:ret_limit])
        for iid, ident in _idents.items():
            email = ident['default-email']
            name = ident['name'] or authors[email]
            result[utils.encrypt(xorkey, iid)] = {
                'name': name,
                'gravatar': hashlib.md5(
                    email.encode(errors='ignore')).hexdigest()}
        result = OrderedDict(
            sorted(list(result.items()), key=lambda t: t[1]['name']))
        return result
