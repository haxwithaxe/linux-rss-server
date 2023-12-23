#!/bin/bash

set -e


CONTEXT="$(dirname "$(realpath "$0")")"

echo context $CONTEXT

docker build \
	--progress plain \
	-t linux-rss-server:latest \
	$@ \
	$CONTEXT 2>&1
