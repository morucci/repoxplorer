# Copyright 2016-2017, Fabien Boucher
# Copyright 2016-2017, Red Hat
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
import copy
import logging

from pecan import conf

from jsonschema import validate as schema_validate

from repoxplorer.index.yamlbackend import YAMLBackend

logger = logging.getLogger(__name__)

contributors_schema = """
$schema: http://json-schema.org/draft-04/schema

definitions:
  group:
    anyOf:
      - type: object
        additionalProperties: false
        properties:
          begin-date:
            type: string
          end-date:
            type: string
      - type: "null"

type: object
properties:
  identities:
    type: object
    additionalProperties: false
    patternProperties:
      ^[0-9]{4}-[0-9]{4}$:
        type: object
        additionalProperties: false
        required:
          - name
          - emails
          - default-email
        properties:
          name:
            type: string
          default-email:
            type: string
            pattern: ^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$
          emails:
            type: object
            additionalProperties: false
            patternProperties:
              ^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$:
                type: object
                additionalProperties: false
                properties:
                  groups:
                    type: object
                    additionalProperties: false
                    patternProperties:
                      ^[a-zA-Z0-9_-]+$:
                        $ref: "#/definitions/group"
"""

contributors_example = """
identities:
  1234-1234:
    name: John Doe
    default-email: jodoe@domain.com
    emails:
      john.doe@domain.com:
        groups:
          acme-10:
            begin-date: 2016/01/01
            end-date: 2016/09/01
          acme-11:
          acme-12:
      jodoe@domain.com:
        groups: {}
  1234-1235:
    name: Jane Doe
    default-email: jane.doe@domain.com
    emails:
      jane.doe@domain.com: {}
      jadoe@domain.com: {}
"""

groups_schema = """
$schema: http://json-schema.org/draft-04/schema

definitions:
  email:
    anyOf:
      - type: object
        additionalProperties: false
        properties:
          begin-date:
            type: string
          end-date:
            type: string
      - type: "null"

type: object
properties:
  groups:
    type: object
    additionalProperties: false
    patternProperties:
      ^[a-zA-Z0-9_-]+$:
        type: object
        additionalProperties: false
        required:
          - description
          - emails
        properties:
          description:
            type: string
          emails:
            type: object
            additionalProperties: false
            patternProperties:
              ^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$:
                $ref: "#/definitions/email"
"""

groups_example = """
groups:
  acme-10:
    description: The group 10 of acme
    emails:
      test@acme.com:
        begin-date: 2016/01/01
        end-date: 2016/09/01
      test2@acme.com:
  acme-11:
    description: The group 11 of acme
    emails:
      test@acme.com:
      test2@acme.com:
      test3@acme.com:
"""


class Contributors(object):
    """ This class manages definition of contributors as
    individual and group level
    """
    def __init__(self, db_path=None, db_default_file=None):
        self.contributors = {}
        self.yback = YAMLBackend(
            db_path or conf.db_path,
            db_default_file=db_default_file or conf.get('db_default_file'))
        self.yback.load_db()
        self.default_data, self.data = self.yback.get_data()
        self._merge()

    def _merge(self):
        """ Merge self.data and inherites from default_data
        """
        merged_idents = {}
        merged_groups = {}
        for d in self.data:
            idents = d.get('identities', {})
            groups = d.get('groups', {})
            merged_idents.update(copy.copy(idents))
            merged_groups.update(copy.copy(groups))

        self.idents = {}
        self.groups = {}
        if self.default_data:
            self.idents = copy.copy(self.default_data.get('identities', {}))
            self.groups = copy.copy(self.default_data.get('groups', {}))

        self.idents.update(merged_idents)
        self.groups.update(merged_groups)

    def validate_idents(self):
        """ Validate self.data consistencies for identities
        """
        issues = []
        ident_ids = set()
        for d in self.data:
            idents = d.get('identities', {})
            try:
                schema_validate({'identities': idents},
                                yaml.load(contributors_schema))
            except Exception, e:
                issues.append(e.message)
                # Schema is wrong pass the rest of the check
                continue
            duplicated = set(idents.keys()) & ident_ids
            if duplicated:
                issues.append("Identity IDs [%s,] are duplicated" % (
                              ",".join(duplicated)))
            ident_ids.update(set(idents.keys()))
            for iid, id_data in idents.items():
                if (id_data['default-email'] not in id_data['emails'].keys()):
                    issues.append("Identity %s default an unknown "
                                  "default-email" % iid)
        return issues

    def validate_groups(self):
        """ Validate self.data consistencies for groups
        """
        issues = []
        group_ids = set()
        for d in self.data:
            groups = d.get('groups', {})
            try:
                schema_validate({'groups': groups},
                                yaml.load(groups_schema))
            except Exception, e:
                issues.append(e.message)
            duplicated = set(groups.keys()) & group_ids
            if duplicated:
                issues.append("Group IDs [%s,] are duplicated" % (
                              ",".join(duplicated)))
            group_ids.update(set(groups.keys()))
        return issues

    def get_idents(self):
        return self.idents

    def get_groups(self):
        return self.groups

    def validate(self):
        self.validate_idents()
        self.validate_groups()

    def get_ident_by_email(self, email):
        idents = self.get_idents()
        selected = filter(lambda ident: email in ident[1].get('emails', []),
                          idents.items())
        if selected:
            return selected[0]
        else:
            # Return a default ident
            return email, {'name': None,
                           'default-email': email,
                           'emails': {email: {}}}

    def get_ident_by_id(self, id):
        idents = self.get_idents()
        return id, idents.get(id)
