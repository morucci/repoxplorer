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


import os
from setuptools import setup
from setuptools import find_packages

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "repoxplorer",
    version = "1.4.1",
    author = "Fabien Boucher",
    author_email = "fabien?dot.boucher@gmail.com",
    description = ("Git repositories metrics"),
    license = "ASL v 2.0",
    keywords = "git metrics statistics stats repo repositories elasticsearch",
    url = "https://github.com/morucci/repoxplorer",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Software Development :: Version Control :: Git",
    ],
    scripts=['bin/repoxplorer-indexer',
             'bin/repoxplorer-config-validate',
             'bin/repoxplorer-fetch-web-assets',
             'bin/repoxplorer-git-credentials-helper',
             'bin/repoxplorer-github-organization'],
)
