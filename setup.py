# -*- coding: utf-8 -*-

import glob

from distutils.core import setup

setup(name='repoxplorer',
    version='0.1',
    description='Git repositories statistics and charts. Cross projects and branches.',
    author='Fabien Boucher',
    author_email='fabien.dot.boucher@gmail.com',
    packages=['repoxplorer', 'repoxplorer.index', 'repoxplorer.index', 'repoxplorer.model',
              'repoxplorer.indexer.git', 'repoxplorer.controllers'],
    data_files=[('bin/', ['el-start.sh', 'el-stop.sh']),
                ('local/share/repoxplorer/public/css/', glob.glob('public/css/*.css')),
                ('local/share/repoxplorer/public/css/images/', glob.glob('public/css/images/*')),
                ('local/share/repoxplorer/public/javascript/', glob.glob('public/javascript/*')),
                ('local/share/repoxplorer/public/images/', glob.glob('public/images/*')),
                ('local/share/repoxplorer/templates/', glob.glob('templates/*')),
                ('local/share/repoxplorer/', ['config.py'])],
)
