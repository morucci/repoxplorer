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

from pecan import expose

from repoxplorer import index
from repoxplorer.controllers import utils
from repoxplorer.index.projects import Projects
from repoxplorer.index.commits import Commits
from repoxplorer.index.contributors import Contributors


class MetadataController(object):

    @expose('json')
    def metadata(self, key=None, pid=None, tid=None, cid=None, gid=None,
                 dfrom=None, dto=None, inc_merge_commit=None,
                 inc_repos=None, exc_groups=None, inc_groups=None):

        c = Commits(index.Connector())
        projects_index = Projects()
        idents = Contributors()

        query_kwargs = utils.resolv_filters(
            projects_index, idents, pid, tid, cid, gid,
            dfrom, dto, inc_repos, inc_merge_commit, None, exc_groups,
            inc_groups)
        del query_kwargs['metadata']

        if not key:
            keys = c.get_metadata_keys(**query_kwargs)
            return keys
        else:
            vals = c.get_metadata_key_values(key, **query_kwargs)
            return vals
