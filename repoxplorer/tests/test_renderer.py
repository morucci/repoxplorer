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


from unittest import TestCase

from repoxplorer.controllers import renderers


class TestCSVRenderer(TestCase):

    def setUp(self):
        self.csvrender = renderers.CSVRenderer(None, None)

    def test_rendering(self):
        data = {'f1': 'd1', 'f2': 2}
        output = self.csvrender.render(None, data)
        print(output)
        self.assertTrue(
            output == "f1,f2\r\nd1,2\r\n")

        data = {'f1': ['e1', 'e2'], 'f2': 2}
        output = self.csvrender.render(None, data)
        self.assertTrue(
            output == "f1,f2\r\ne1;e2,2\r\n")

        data = [
            {'f1': 'd1', 'f2': 2},
            {'f1': 'd2', 'f2': 3},
        ]

        output = self.csvrender.render(None, data)
        self.assertTrue(
            output == "f1,f2\r\nd1,2\r\nd2,3\r\n")

        data = {'f1': {}}
        self.assertRaises(ValueError, self.csvrender.render, None, data)
