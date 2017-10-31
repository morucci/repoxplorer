import csv
from StringIO import StringIO


class CSVRenderer(object):
    def __init__(self, path, extra_vars):
        pass

    def render(self, template_path, namespace):
        buf = StringIO()
        # Assume namespace an array of dict
        if not isinstance(namespace, list):
            namespace = [namespace]
        for e in namespace:
            assert isinstance(e, dict)
        keys = namespace[0].keys()
        w = csv.DictWriter(buf, fieldnames=keys)
        w.writeheader()
        for e in namespace:
            d = {}
            for k, v in e.items():
                if isinstance(v, unicode):
                    d[k] = v.encode('utf-8', 'ignore')
                else:
                    d[k] = v
            w.writerow(d)
        buf.seek(0)
        return buf.read()
