FROM fedora:29
LABEL maintainer="fabien.dot.boucher@gmail.com"

ARG version=changes/22/15122/7

RUN rpm --import https://artifacts.elastic.co/GPG-KEY-elasticsearch
ADD elasticsearch.repo /etc/yum.repos.d/elasticsearch.repo

RUN dnf -y install sudo elasticsearch java-1.8.0-openjdk libffi-devel \
    openssl-devel python3-devel git gcc supervisor
RUN dnf -y update
RUN dnf clean all
RUN rm -rf /var/cache/yum /var/cache/dnf

RUN mkdir /etc/repoxplorer
RUN git clone https://softwarefactory-project.io/r/repoxplorer
RUN cd repoxplorer && git fetch origin ${version}
RUN cd repoxplorer && git checkout FETCH_HEAD
RUN cd repoxplorer && python3 -m pip install -r requirements.txt && python3 -m pip install .
RUN cd repoxplorer && cp config.py /etc/repoxplorer/
RUN cd repoxplorer && python3 ./bin/repoxplorer-fetch-web-assets --config /etc/repoxplorer/config.py

RUN mkdir /etc/repoxplorer/defs
RUN sed -i "s|^db_path =.*|db_path = '/etc/repoxplorer/defs'|" /etc/repoxplorer/config.py

ADD ./supervisord.conf /etc/supervisord.conf

EXPOSE 51000

CMD ["supervisord", "-n", "-c", "/etc/supervisord.conf"]
