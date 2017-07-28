#
# Copyright (c) 2017 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os
import logging
import yaml

logger = logging.getLogger(__name__)


class NoDatesSafeLoader(yaml.SafeLoader):
    @classmethod
    def remove_implicit_resolver(cls, tag_to_remove):
        """
        We want to load datetimes as strings, not dates, because we
        go on to serialise as json which doesn't have the advanced types
        of yaml, and leads to incompatibilities down the track.
        """
        if 'yaml_implicit_resolvers' not in cls.__dict__:
            cls.yaml_implicit_resolvers = cls.yaml_implicit_resolvers.copy()

            for first_letter, mappings in cls.yaml_implicit_resolvers.items():
                cls.yaml_implicit_resolvers[first_letter] = [
                    (tag, regexp)
                    for tag, regexp in mappings
                    if tag != tag_to_remove]


NoDatesSafeLoader.remove_implicit_resolver('tag:yaml.org,2002:timestamp')


class YAMLDBException(Exception):
    pass


class YAMLBackend(object):
    def __init__(self, db_path, db_default_file=None):
        """ Class to read YAML files from a DB path.
        db_default_file: is the path to a trusted file usually
            computed from an already verified data source.
        db_path: directory where data can be read. This is
            supposed to be user provided data to be verified
            by the caller and could overwrite data from the
            default_file.
        """
        self.db_path = db_path
        self.db_default_file = db_default_file
        self.default_data = None
        self.data = []

    def load_db(self):
        def check_ext(f):
            return f.endswith('.yaml') or f.endswith('.yml')

        def load(path):
            logger.debug("Reading %s ..." % path)
            try:
                data = yaml.load(file(path), Loader=NoDatesSafeLoader)
            except:
                raise YAMLDBException(
                    "YAML format corrupted in file %s" % (path))
            return data

        if self.db_default_file:
            self.default_data = load(self.db_default_file)
        yamlfiles = [f for f in os.listdir(self.db_path) if check_ext(f)]
        for f in yamlfiles:
            path = os.path.join(self.db_path, f)
            if path == self.db_default_file:
                continue
            self.data.append(load(path))

    def get_data(self):
        """ Return the full raw data structure.
        """
        return self.default_data, self.data
