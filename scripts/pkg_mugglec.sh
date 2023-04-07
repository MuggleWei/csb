#!/bin/bash

if [ "$#" -lt 1 ]; then
	echo "Usage: $0 <Debug|Release>"
	echo "build without specify build type, use release by default"
	BUILD_TYPE=release
else
	# to lowercase
	BUILD_TYPE=$(echo $1 | tr '[:upper:]' '[:lower:]')
fi

lpb build \
	-c etc/metas/mugglec/mugglec.yml \
	-p GIT_TAG=v1.0.0 \
	-p BUILD_TYPE=$BUILD_TYPE \
	-o ./artifacts
