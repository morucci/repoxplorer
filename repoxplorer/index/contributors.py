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
import logging

from pecan import conf

logger = logging.getLogger(__name__)


class Contributors(object):
    def __init__(self):
        path = conf.idents_file_path
        self.contributors = {}
        try:
            self.contributors = yaml.load(file(path)) or {}
        except Exception, e:
            logger.error(
                'Unable to read idents.yaml (%s). Default is empty.' % e)
        self.idents = {}

    def get_contributors(self):
        for cont in self.contributors:
            main_email = cont['emails'][0]
            self.idents[main_email] = (main_email,
                                       cont['name'],
                                       cont['emails'])
            for email in cont['emails'][1:]:
                self.idents[email] = (main_email,
                                      cont['name'],
                                      cont['emails'])
        return self.idents
