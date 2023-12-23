FROM python:3.12-alpine

COPY entrypoint.sh /entrypoint.sh
RUN chmod 755 /entrypoint.sh
ENTRYPOINT /entrypoint.sh

RUN apk add --no-cache py3-lxml
COPY ./dist/linux_rss_server*.tar.gz /linux_rss_server.tar.gz
RUN pip install /linux_rss_server.tar.gz && rm /linux_rss_server.tar.gz
