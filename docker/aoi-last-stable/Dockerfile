FROM centos:7
LABEL maintainer="fabien.dot.boucher@gmail.com"

ARG version=1.4.0

RUN rpm --import https://packages.elastic.co/GPG-KEY-elasticsearch
ADD elasticsearch.repo /etc/yum.repos.d/elasticsearch.repo

RUN yum -y install sudo elasticsearch java-1.8.0-openjdk libffi-devel openssl-devel python-devel git gcc
RUN yum -y update
RUN yum clean all
RUN rm -rf /var/cache/yum

RUN curl "https://bootstrap.pypa.io/get-pip.py" -o "get-pip.py"
RUN python get-pip.py
RUN rm get-pip.py

RUN git clone https://github.com/morucci/repoxplorer
RUN cd repoxplorer && git checkout ${version}
RUN cd repoxplorer && pip install -r requirements.txt && pip install .
RUN cd repoxplorer && ./bin/repoxplorer-fetch-web-assets -p /usr/local/share/repoxplorer/public/

RUN mkdir -p /etc/repoxplorer/defs
RUN sed -i "s|^db_path =.*|db_path = '/etc/repoxplorer/defs'|" /usr/local/share/repoxplorer/config.py

RUN pip install supervisor
ADD ./supervisord.conf /etc/supervisord.conf

EXPOSE 51000

CMD ["supervisord", "-n", "-c", "/etc/supervisord.conf"]
