#!/bin/sh

RSS_SERVER_CONFIG="${RSS_SERVER_CONFIG:-/etc/linux_rss_server/config.yml}"

/usr/local/bin/linux_rss_server --config $RSS_SERVER_CONFIG
