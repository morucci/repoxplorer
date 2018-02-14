FROM centos:7
LABEL maintainer="fabien.dot.boucher@gmail.com"

RUN yum -y install epel-release

RUN rpm --import https://packages.elastic.co/GPG-KEY-elasticsearch
ADD elasticsearch.repo /etc/yum.repos.d/elasticsearch.repo

RUN yum -y install supervisor elasticsearch java-1.8.0-openjdk sudo
RUN yum install -y https://github.com/morucci/repoxplorer/releases/download/1.2.0/repoxplorer-1.2.0-1.el7.centos.noarch.rpm
RUN yum -y update
RUN yum clean all
RUN rm -rf /var/cache/yum

RUN /usr/bin/repoxplorer-fetch-web-assets -p /usr/share/repoxplorer/public/

RUN mkdir /etc/repoxplorer/defs
RUN sed -i "s|^db_path =.*|db_path = '/etc/repoxplorer/defs'|" /etc/repoxplorer/config.py

ADD ./supervisord.conf /etc/supervisord.conf

EXPOSE 51000

CMD ["supervisord", "-n"]
