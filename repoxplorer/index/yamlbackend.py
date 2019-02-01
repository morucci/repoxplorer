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
import yaml
import pickle
import logging

from Crypto.Hash import SHA

from pecan import conf


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
    def __init__(self, db_path, db_default_file=None, db_cache_path=None):
        """ Class to read YAML files from a DB path.
        db_default_file: is the path to a trusted file usually
            computed from an already verified data source.
        db_path: directory where data can be read. This is
            supposed to be user provided data to be verified
            by the caller and could overwrite data from the
            default_file.
        db_cache_path: directory to store cache files
        """
        self.db_path = db_path or conf.get('db_path')
        self.db_default_file = db_default_file
        self.db_cache_path = (
            db_cache_path or conf.get('db_cache_path') or self.db_path)

        self.default_data = None
        self.data = []
        # List of hashes
        self.hashes = []

    def load_db(self):
        def check_ext(f):
            return f.endswith('.yaml') or f.endswith('.yml')

        def load(path):
            data = None
            logger.debug("Check cache for %s ..." % path)
            basename = os.path.basename(path)
            if not os.path.isdir(self.db_path):
                os.makedirs(self.db_path)
            if self.db_cache_path and not os.path.isdir(self.db_cache_path):
                os.makedirs(self.db_cache_path)
            cached_hash_path = os.path.join(
                self.db_cache_path, basename + '.hash')
            cached_data_path = os.path.join(
                self.db_cache_path, basename + '.cached')
            hash = SHA.new(open(path).read().encode(
                errors='ignore')).hexdigest()
            if (os.path.isfile(cached_hash_path) and
                    os.path.isfile(cached_data_path)):
                cached_hash = pickle.load(open(cached_hash_path, 'rb'))
                if cached_hash == hash:
                    logger.debug("Reading %s from cache ..." % path)
                    data = pickle.load(open(cached_data_path, 'rb'))
                    self.hashes.append(hash)
            if not data:
                logger.debug("Reading %s from file ..." % path)
                try:
                    data = yaml.load(
                        open(path, 'rb'), Loader=NoDatesSafeLoader)
                except Exception as e:
                    raise YAMLDBException(
                        "YAML format corrupted in file %s (%s)" % (path, e))
                pickle.dump(
                    data, open(cached_data_path, 'wb'),
                    pickle.HIGHEST_PROTOCOL)
                pickle.dump(
                    hash, open(cached_hash_path, 'wb'),
                    pickle.HIGHEST_PROTOCOL)
                self.hashes.append(hash)
            return data

        if self.db_default_file:
            self.default_data = load(self.db_default_file)

        yamlfiles = [f for f in os.listdir(self.db_path) if check_ext(f)]
        yamlfiles.sort()
        for f in yamlfiles:
            path = os.path.join(self.db_path, f)
            if path == self.db_default_file:
                continue
            self.data.append(load(path))

    def get_data(self):
        """ Return the full raw data structure.
        """
        return self.default_data, self.data
