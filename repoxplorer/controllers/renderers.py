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

import csv
from io import StringIO


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
        keys = list(namespace[0].keys())
        keys.sort()
        w = csv.DictWriter(buf, fieldnames=keys)
        w.writeheader()
        for e in namespace:
            d = {}
            for k, v in list(e.items()):
                if not any([
                        isinstance(v, str),
                        isinstance(v, list),
                        isinstance(v, int),
                        isinstance(v, float)]):
                    raise ValueError(
                        "'%s' (type: %s) is not supported for CSV output" % (
                            str(v), type(v)))
                if isinstance(v, str):
                    d[k] = v.encode('utf-8', 'ignore')
                elif isinstance(v, list):
                    d[k] = ";".join(v)
                else:
                    d[k] = str(v)
            w.writerow(d)
        buf.seek(0)
        return buf.read()
