#!/bin/bash
# Publish the latest build as the current git tag or the value of the
#   environment variable $TAG

set -e

DEST_IMAGE="haxwithaxe/linux-rss-server"
SRC_IMAGE="linux-rss-server"
TAG=${1:-${TAG:-$(git tag --points-at HEAD)}}

if [[ -z $TAG ]]; then
	echo No tag set. Either set the \$TAG environment variable or add a tag to HEAD. 1>&2
	exit 1
fi

echo Tagging ${SRC_IMAGE} as $TAG
if [[ "$TAG" != *"-"* ]]; then
	docker image tag ${SRC_IMAGE}:latest ${DEST_IMAGE}:latest
fi
docker image tag ${SRC_IMAGE}:latest ${DEST_IMAGE}:$TAG
echo Pushing ${DEST_IMAGE}:latest and $TAG
if [[ "$TAG" != *"-"* ]]; then
	docker image push ${DEST_IMAGE}:latest
fi
docker image push ${DEST_IMAGE}:$TAG
