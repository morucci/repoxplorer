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

from pecan import conf

from repoxplorer import index
from repoxplorer.index import YAMLDefinition
from repoxplorer.index import date2epoch
from repoxplorer.index import users
from datetime import datetime

user_endpoint_active = conf.get('users_endpoint', False)
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
      ^.+$:
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
            pattern: ^.+@.+$
          emails:
            type: object
            additionalProperties: false
            patternProperties:
              ^.+@.+$:
                type: object
                additionalProperties: false
                properties:
                  groups:
                    type: object
                    additionalProperties: false
                    patternProperties:
                      ^.+$:
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
            begin-date: 2016-01-01
            end-date: 2016-01-09
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
      ^.+$:
        type: object
        additionalProperties: false
        required:
          - description
          - emails
        properties:
          description:
            type: string
          domains:
            type: array
            uniqueItems: true
            items:
              type: string
          emails:
            type: object
            additionalProperties: false
            patternProperties:
              ^.+@.+$:
                $ref: "#/definitions/email"
"""

groups_example = """
groups:
  acme-10:
    description: The group 10 of acme
    emails:
      test@acme.com:
        begin-date: 2016-01-01
        end-date: 2016-01-01
      test2@acme.com:
    domains:
      - acme10.org
      - acme.org
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
    def __init__(self, db_path=None, db_default_file=None, vonly=False):
        YAMLDefinition.__init__(self, db_path, db_default_file)
        self.enriched_groups = False
        self.enriched_idents = False
        if not vonly:
            self._users = users.Users(
                index.Connector(index_suffix='users'))

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
        groups are also populated by idents defining
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
                    else:
                        data[key] = None
        # Here if the users elk backend is active we populate groups
        # by querying the users index
        if user_endpoint_active:
            for gid, groups in self.groups.items():
                idents = self._users.get_idents_in_group(gid)
                for ident in idents:
                    _, data = self.backend_convert_ident(ident)
                    for email, email_data in data['emails'].items():
                        for group, details in email_data.get(
                                'groups', {}).items():
                            if group == gid:
                                add_to_group(group, email, details)
        # If not regular yaml identities index is used
        else:
            for iid, id_data in self.idents.items():
                for email, email_data in id_data['emails'].items():
                    for group, details in email_data.get(
                            'groups', {}).items():
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
                        else:
                            data[key] = None
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
                                    datetime.strptime(data[key], "%Y-%m-%d")
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
                            datetime.strptime(data[key], "%Y-%m-%d")
                except Exception:
                    issues.append("Group %s declares email %s "
                                  "membership invalid date %s" % (
                                      gid, email, data))
        return issues

    def _get_idents(self):
        if not self.enriched_idents:
            self._enrich_idents()
        return self.idents

    def validate(self):
        validation_issues = []
        validation_issues.extend(self._validate_groups())
        validation_issues.extend(self._validate_idents())
        return validation_issues

# Below are methods specific to elk users model to be compatible
# with calling methods

    def backend_convert_ident(self, ident):
        # Transform the data structure to be compatible
        data = {}
        data['name'] = ident['name']
        data['default-email'] = ident['default-email']
        data['emails'] = {}
        for email in ident['emails']:
            groups = {}
            data['emails'][email['email']] = {'groups': groups}
            if 'groups' in email.keys():
                for group in email['groups']:
                    groups[group['group']] = {}
                    for elm in ('begin-date', 'end-date'):
                        if elm in group.keys():
                            groups[group['group']][elm] = group[elm]
        return ident['uid'], data

# Below are top level methods for the yaml or the elk backend

    def get_idents_by_emails(self, emails):
        if not isinstance(emails, list):
            emails = [emails]

        _selecteds = []
        if user_endpoint_active:
            # Look at the elk backend
            if emails:
                # Do not request if emails is empty (ELK backend will return
                # all ident in that case)
                el_selecteds = self._users.get_idents_by_emails(emails)
                emails_not_found = set(emails)
                for ident in el_selecteds:
                    ident = self.backend_convert_ident(ident)
                    _selecteds.append(ident)
                    emails_not_found -= set(ident[1]['emails'].keys())
                for email in emails_not_found:
                    _selecteds.append(
                        (email, {'name': None,
                                 'default-email': email,
                                 'emails': {email: {}}})
                        )
        else:
            # Look at the yaml backend
            idents = self._get_idents()
            found = set()
            for email in emails:
                if email in found:
                    continue
                for uid in idents:
                    if email in idents[uid].get('emails', {}):
                        _selecteds.append((uid, copy.deepcopy(idents[uid])))
                        found.add(email)
                        break
                if email not in found:
                    _selecteds.append(
                        (email, {'name': None,
                                 'default-email': email,
                                 'emails': {email: {}}})
                    )

        selecteds = {}
        for uid, data in _selecteds:
            selecteds[uid] = data

        if len(emails) == 1 and len(selecteds) > 1:
            raise Exception("More than one idents matched the requested email")
        return selecteds

    def get_ident_by_id(self, id):
        if user_endpoint_active:
            ident = self._users.get_ident_by_id(id)
            if ident:
                id, ident = self.backend_convert_ident(ident)
        else:
            ident = self._get_idents().get(id)
            ident = copy.deepcopy(ident)
        if not ident:
            return id, None
        else:
            return id, ident

    def get_groups(self):
        if not self.enriched_idents:
            self._enrich_idents()
        if not self.enriched_groups:
            self._enrich_groups()
        return self.groups

    def get_group_by_id(self, id):
        groups = self.get_groups()
        return id, copy.deepcopy(groups.get(id))
