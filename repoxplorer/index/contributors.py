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


import copy
import logging

from repoxplorer.index import YAMLDefinition
from repoxplorer.index import date2epoch
from datetime import datetime


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
            begin-date: 01/01/2016
            end-date: 09/01/2016
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
        begin-date: 01/01/2016
        end-date: 09/01/2016
      test2@acme.com:
  acme-11:
    description: The group 11 of acme
    emails:
      test@acme.com:
      test2@acme.com:
      test3@acme.com:
"""


class Contributors(YAMLDefinition):
    """ This class manages definition of contributors as
    individual and group level
    """
    def __init__(self, db_path=None, db_default_file=None):
        YAMLDefinition.__init__(self, db_path, db_default_file)
        self.enriched_groups = False
        self.enriched_idents = False

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

    def _enrich_groups(self):
        """ Here we convert provided date to epoch and
        groups are also populated by by idents defining
        an ownership to a group
        """
        def add_to_group(group, email, details):
            if group not in self.groups.keys():
                return
            self.groups[group]['emails'][email] = details
        for gid, groups in self.groups.items():
            for email, data in groups['emails'].items():
                if not data:
                    continue
                for key in ('begin-date', 'end-date'):
                    if key in data:
                        data[key] = date2epoch(data[key])
        for iid, id_data in self.idents.items():
            for email, email_data in id_data['emails'].items():
                for group, details in email_data.get('groups', {}).items():
                    add_to_group(group, email, details)
        self.enriched_groups = True

    def _enrich_idents(self):
        """ Here we convert provided date to epoch
        """
        for iid, id_data in self.idents.items():
            for email, email_data in id_data['emails'].items():
                for group, data in email_data.get('groups', {}).items():
                    if not data:
                        continue
                    for key in ('begin-date', 'end-date'):
                        if key in data:
                            data[key] = date2epoch(data[key])
        self.enriched_idents = True

    def _validate_idents(self):
        """ Validate self.data consistencies for identities
        """
        _, issues = self._check_basic('identities',
                                      contributors_schema,
                                      'Identity')
        if issues:
            return issues
        # Check uncovered by the schema validator
        known_groups = self.groups.keys()
        for d in self.data:
            idents = d.get('identities', {})
            for iid, id_data in idents.items():
                if (id_data['default-email'] not in id_data['emails'].keys()):
                    issues.append("Identity %s default an unknown "
                                  "default-email" % iid)
                _groups = [g.get('groups', {}).keys() for g in
                           id_data['emails'].values()]
                groups = set()
                for gs in _groups:
                    groups.update(set(gs))
                if not groups.issubset(set(known_groups)):
                    issues.append("Identity %s declares membership to "
                                  "an unknown group" % iid)
                for email, email_data in id_data['emails'].items():
                    for group, data in email_data.get('groups', {}).items():
                        if not data:
                            continue
                        try:
                            for key in ('begin-date', 'end-date'):
                                if key in data:
                                    datetime.strptime(data[key], "%m/%d/%Y")
                        except Exception:
                            issues.append("Identity %s declares group %s "
                                          "membership invalid date %s" % (
                                              iid, group, data))
        return issues

    def _validate_groups(self):
        """ Validate self.data consistencies for groups
        """
        _, issues = self._check_basic('groups',
                                      groups_schema,
                                      'Group')
        if issues:
            return issues
        # Check uncovered by the schema validator
        for gid, groups in self.groups.items():
            for email, data in groups['emails'].items():
                if not data:
                    continue
                try:
                    for key in ('begin-date', 'end-date'):
                        if key in data:
                            datetime.strptime(data[key], "%m/%d/%Y")
                except Exception:
                    issues.append("Group %s declares email %s "
                                  "membership invalid date %s" % (
                                      gid, email, data))
        return issues

    def get_idents(self):
        if not self.enriched_idents:
            self._enrich_idents()
        return self.idents

    def get_groups(self):
        if not self.enriched_idents:
            self._enrich_idents()
        if not self.enriched_groups:
            self._enrich_groups()
        return self.groups

    def validate(self):
        validation_issues = []
        validation_issues.extend(self._validate_groups())
        validation_issues.extend(self._validate_idents())
        return validation_issues

    def get_ident_by_email(self, email):
        idents = self.get_idents()
        selected = filter(lambda ident: email in ident[1].get('emails', []),
                          idents.items())
        if selected:
            return copy.deepcopy(selected[0])
        else:
            # Return a default ident
            return email, {'name': None,
                           'default-email': email,
                           'emails': {email: {}}}

    def get_ident_by_id(self, id):
        idents = self.get_idents()
        return id, copy.deepcopy(idents.get(id))
