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


import yaml
import time
import pytz
import datetime

from pecan import conf

from Crypto.Hash import SHA

from elasticsearch import client
from jsonschema import validate as schema_validate

from repoxplorer.index.yamlbackend import YAMLBackend


def date2epoch(date):
    d = datetime.datetime.strptime(date, "%Y-%m-%d")
    d = d.replace(tzinfo=pytz.utc)
    epoch = (d - datetime.datetime(1970, 1, 1,
                                   tzinfo=pytz.utc)).total_seconds()
    return int(epoch)


def get_elasticsearch_version(es):
    version = es.info()['version']['number']
    return int(version.split('.')[0])


def add_params(es):
    if get_elasticsearch_version(es) >= 7:
        return {'include_type_name': 'true'}
    else:
        return {}


# From https://stackoverflow.com/a/27974027/1966658
def clean_empty(d):
    if not isinstance(d, (dict, list)):
        return d
    if isinstance(d, list):
        return [v for v in (clean_empty(v) for v in d) if v]
    return {k: v for k, v in ((k, clean_empty(v)) for k, v in d.items()) if (
        v or v == False)}  # noqa: E712


class Connector(object):
    def __init__(self, host=None, port=None, index=None, index_suffix=None):
        self.host = (host or
                     getattr(conf, 'elasticsearch_host', None) or
                     'localhost')
        self.port = (port or
                     getattr(conf, 'elasticsearch_port', None) or
                     9200)
        self.index = (index or
                      getattr(conf, 'elasticsearch_index', None) or
                      'repoxplorer')
        if index_suffix:
            self.index += "-%s" % index_suffix
        if getattr(conf, 'elasticsearch_user', None) and getattr(conf,
                'elasticsearch_password', None):
            self.http_auth = "%s:%s" % (
                    getattr(conf, 'elasticsearch_user',None),
                    getattr(conf,'elasticsearch_password', None))
            self.es = client.Elasticsearch(
                [{"host": self.host, "port": self.port,
                  "http_auth": self.http_auth}], timeout=60)
        else:
            self.es = client.Elasticsearch(
                [{"host": self.host, "port": self.port}],
                timeout=60)
        self.ic = client.IndicesClient(self.es)
        if not self.ic.exists(index=self.index):
            self.ic.create(index=self.index)
            # Give some time to have the index fully created
            time.sleep(1)


class YAMLDefinition(object):
    def __init__(self, db_path=None, db_default_file=None,
                 db_cache_path=None):
        db_cache_path = db_cache_path or conf.get('db_cache_path') or db_path
        self.yback = YAMLBackend(
            db_path or conf.get('db_path'),
            db_default_file=db_default_file or conf.get('db_default_file'),
            db_cache_path=db_cache_path)
        self.yback.load_db()
        self.hashes_str = SHA.new(
            "".join(self.yback.hashes).encode(errors='ignore')).hexdigest()
        self.default_data, self.data = self.yback.get_data()
        self._merge()

    def _check_basic(self, key, schema, identifier):
        """ Verify schema and no data duplicated
        """
        issues = []
        ids = set()
        for d in self.data:
            data = d.get(key, {})
            try:
                schema_validate({key: data},
                                yaml.load(schema))
            except Exception as e:
                issues.append(e.message)
            duplicated = set(data.keys()) & ids
            if duplicated:
                issues.append("%s IDs [%s,] are duplicated" % (
                              identifier, ",".join(duplicated)))
            ids.update(set(data.keys()))
        return ids, issues
