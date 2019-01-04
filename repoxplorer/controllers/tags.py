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

from repoxplorer.controllers import utils
from repoxplorer import index
from repoxplorer.index.projects import Projects
from repoxplorer.index.tags import Tags
from repoxplorer.index.contributors import Contributors


class TagsController(object):

    @expose('json')
    def tags(self, pid=None, tid=None,
             dfrom=None, dto=None, inc_repos=None):
        t = Tags(index.Connector())
        projects_index = Projects()
        idents = Contributors()

        query_kwargs = utils.resolv_filters(
            projects_index, idents, pid, tid, None, None,
            dfrom, dto, inc_repos, None, None, None, None)

        p_filter = [":".join(r.split(':')[:-1]) for r in query_kwargs['repos']]
        dfrom = query_kwargs['fromdate']
        dto = query_kwargs['todate']
        ret = [r['_source'] for r in t.get_tags(p_filter, dfrom, dto)]
        # TODO: if tid is given we can include user defined releases
        # for repo tagged with tid.
        if not pid:
            return ret
        # now append user defined releases
        ur = {}
        project = projects_index.get_projects()[pid]
        for repo in project['refs']:
            if 'releases' in repo:
                for release in repo['releases']:
                    ur[release['name']] = {'name': release['name'],
                                           'date': release['date']}
        for rel in ur.values():
            ret.append(rel)
        return ret
