# Copyright 2019, Red Hat
# Copyright 2019, Fabien Boucher
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

import re

METADATA_REs = {
    'signed-of-by': re.compile('^[Ss]igned-[Oo]f(?:-[Bb]y)?:([^//].+)$'),
    'reviewed-by': re.compile('^[Rr]evied(?:-[Bb]y)?:([^//].+)$'),
    'tested-by': re.compile('^[Tt]ested(?:-[Bb]y)?:([^//].+)$'),
    'rebased-by': re.compile('^[Rr]ebased(?:-[Bb]y)?:([^//].+)$'),
    'reported-by': re.compile('^[Rr]eported(?:-[Bb]y)?:([^//].+)$'),
    'co-authored-by': re.compile('^[Cc]o-[Aa]uthored(?:-[Bb]y)?:([^//].+)$'),
    'helped-by': re.compile('^[Hh]elped(?:-[Bb]y)?:([^//].+)$'),
    'acked-by': re.compile('^[Aa]cked(?:-[Bb]y)?:([^//].+)$'),
    'suggested-by': re.compile('^[Ss]uggested(?:-[Bb]y)?:([^//].+)$'),
    'noticed-by': re.compile('^[Nn]oticed(?:-[Bb]y)?:([^//].+)$'),
    'mentored-by': re.compile('^[Mm]entored(?:-[Bb]y)?:([^//].+)$'),
    'tested-by': re.compile('^[Tt]ested(?:-[Bb]y)?:([^//].+)$'),
    'closes-bug': re.compile('^[Cc]loses?(?:-[Bb]ug)?:([^//].+)$'),
    'fixes-bug': re.compile('^[Ff]ixe?s?(?:-[Bb]ug)?:([^//].+)$'),
    'related-bug': re.compile('^[Rr]elated(?:-[Bb]ug)?:([^//].+)$'),
    'depends-on': re.compile('^[Dd]epends(?:-[Oo]n)?:([^//].+)$'),
    'resolves': re.compile('^[Rr]esolv(?:es)?:([^//].+)$'),
    'issue': re.compile('^[Ii]ssue:([^//].+)$'),
    'story': re.compile('^[Ss]tory:([^//].+)$'),
    'task': re.compile('^[Tt]ask:([^//].+)$'),
    'bug': re.compile('^[Bu]ug:([^//].+)$'),
}
