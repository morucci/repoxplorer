#!/bin/bash

spectool -gf -S repoxplorer.spec
mock -r /etc/mock/epel-7-x86_64.cfg --buildsrpm --sources . --spec repoxplorer.spec 
mock -r /etc/mock/epel-7-x86_64.cfg --copyout /builddir/build/SRPMS/repoxplorer-0.8.0-1.el7.centos.src.rpm .
mock -r /etc/mock/epel-7-x86_64.cfg -i --rebuild repoxplorer-0.8.0-1.el7.centos.src.rpm 
mock -r /etc/mock/epel-7-x86_64.cfg --copyout /builddir/build/RPMS/repoxplorer-0.8.0-1.el7.centos.noarch.rpm .
