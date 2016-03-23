import time

from elasticsearch import client


class Connector(object):
    def __init__(self, host='localhost', port=9200):
        self.host = host
        self.port = port
        self.index = 'repoxplorer'
        self.es = client.Elasticsearch([{"host": self.host,
                                         "port": self.port}])
        self.ic = client.IndicesClient(self.es)
        if not self.ic.exists(index=self.index):
            self.ic.create(index=self.index)
            time.sleep(0.1)
