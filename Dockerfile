FROM python:3.12-alpine

COPY entrypoint.sh /entrypoint.sh
RUN chmod 755 /entrypoint.sh
ENTRYPOINT /entrypoint.sh

RUN mkdir -p /linux_rss_server/cache
COPY ./default-config.yml /linux_rss_server/config.yml

# Installing lxml here to avoid building it with pip
RUN apk add --no-cache py3-lxml
COPY ./dist/linux_rss_server*.tar.gz /linux_rss_server.tar.gz
RUN pip install /linux_rss_server.tar.gz && rm /linux_rss_server.tar.gz
