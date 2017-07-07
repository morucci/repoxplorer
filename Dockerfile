FROM centos:7
MAINTAINER "Fabien Boucher" <fabien.dot.boucher@gmail.com>

RUN yum -y install epel-release

RUN rpm --import https://packages.elastic.co/GPG-KEY-elasticsearch
ADD elasticsearch.repo /etc/yum.repos.d/elasticsearch.repo
RUN yum -y install supervisor elasticsearch java-1.8.0-openjdk sudo
RUN sed -i s/.*ES_HEAP_SIZE=.*/ES_HEAP_SIZE=2g/ /etc/sysconfig/elasticsearch

RUN yum install -y https://github.com/morucci/repoxplorer/releases/download/0.9.0/repoxplorer-0.9.0-1.el7.centos.noarch.rpm
RUN /usr/bin/repoxplorer-fetch-web-assets -p /usr/share/repoxplorer/public/

ADD ./supervisord.conf /etc/supervisord.conf

EXPOSE 51000

CMD ["supervisord", "-n"]
