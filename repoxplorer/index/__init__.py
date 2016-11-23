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


import time

from pecan import conf

from elasticsearch import client


class Connector(object):
    def __init__(self, host=None, port=None, index=None):
        self.host = (host or
                     getattr(conf, 'elasticsearch_host', None) or
                     'localhost')
        self.port = (port or
                     getattr(conf, 'elasticsearch_port', None) or
                     9200)
        self.index = (index or
                      getattr(conf, 'elasticsearch_index', None) or
                      'repoxplorer')
        self.es = client.Elasticsearch([{"host": self.host,
                                         "port": self.port}])
        self.ic = client.IndicesClient(self.es)
        if not self.ic.exists(index=self.index):
            self.ic.create(index=self.index)
            # Give some time to have the index fully created
            time.sleep(1)
