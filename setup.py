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


import glob

from distutils.core import setup

setup(name='repoxplorer',
      version='0.4',
      description='Git repositories statistics and charts.',
      author='Fabien Boucher',
      author_email='fabien.dot.boucher@gmail.com',
      packages=['repoxplorer', 'repoxplorer.index', 'repoxplorer.index',
                'repoxplorer.model', 'repoxplorer.indexer',
                'repoxplorer.indexer.git', 'repoxplorer.controllers'],
      scripts=['bin/repoxplorer-indexer'],
      data_files=[('bin/', ['bin/el-start.sh', 'bin/el-stop.sh']),
                  ('local/share/repoxplorer/',
                   glob.glob('etc/*')),
                  ('local/share/repoxplorer/public/css/',
                   glob.glob('public/css/*.css')),
                  ('local/share/repoxplorer/public/css/images/',
                   glob.glob('public/css/images/*')),
                  ('local/share/repoxplorer/public/javascript/',
                   glob.glob('public/javascript/*')),
                  ('local/share/repoxplorer/public/images/',
                   glob.glob('public/images/*')),
                  ('local/share/repoxplorer/templates/',
                   glob.glob('templates/*')),
                  ('local/share/repoxplorer/', ['config.py'])])
