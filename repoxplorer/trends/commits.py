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


import logging

from repoxplorer.index.commits import Commits

logger = logging.getLogger(__name__)


class CommitsAmountTrend(object):
    def __init__(self, connector=None):
        self.ic = Commits(connector)

    def get_trend(self, mails=[], repos=[],
                  period_a=None, period_b=None,
                  merge_commit=None):
        """ Return the amount diff and the percentil
        of amount evolution for perdiod a compared to
        period b
        """
        assert isinstance(period_a, tuple)
        assert isinstance(period_b, tuple)
        c_amnt_a = self.ic.get_commits_amount(mails, repos,
                                              period_a[0], period_a[1],
                                              merge_commit)
        c_amnt_b = self.ic.get_commits_amount(mails, repos,
                                              period_b[0], period_b[1],
                                              merge_commit)
        diff = c_amnt_a - c_amnt_b
        trend = diff * 100 / (c_amnt_a or c_amnt_b)
        return diff, trend
