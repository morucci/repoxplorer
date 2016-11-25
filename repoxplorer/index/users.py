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


# TODO: Should be called Contributors instead
class Users(object):
    def __init__(self):
        path = conf.idents_file_path
        self.users = {}
        try:
            self.users = yaml.load(file(path)) or {}
        except Exception, e:
            logger.error(
                'Unable to read idents.yaml (%s). Default is empty.' % e)
        self.idents = {}

    def get_users(self):
        for user in self.users:
            main_email = user['emails'][0]
            self.idents[main_email] = (main_email,
                                       user['name'],
                                       user['emails'])
            for email in user['emails'][1:]:
                self.idents[email] = (main_email,
                                      user['name'],
                                      user['emails'])
        return self.idents
