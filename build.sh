#!/bin/bash

version=$1

spectool -gf -S repoxplorer.spec
mock -r /etc/mock/epel-7-x86_64.cfg --buildsrpm --sources . --spec repoxplorer.spec 
mock -r /etc/mock/epel-7-x86_64.cfg --copyout /builddir/build/SRPMS/repoxplorer-${version}.el7.src.rpm .
mock -r /etc/mock/epel-7-x86_64.cfg -i --rebuild repoxplorer-${version}.el7.src.rpm
mock -r /etc/mock/epel-7-x86_64.cfg --copyout /builddir/build/RPMS/repoxplorer-${version}.el7.noarch.rpm .
