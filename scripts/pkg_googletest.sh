#!/bin/bash

if [ "$#" -lt 1 ]; then
	echo "Usage: build.sh <Debug|Release>"
	echo "build without specify build type, use release by default"
	BUILD_TYPE=release
else
	# to lowercase
	BUILD_TYPE=$(echo $1 | tr '[:upper:]' '[:lower:]')
fi

./lpb build -c etc/metas/googletest.yml -p GIT_TAG=v1.13.0 -p BUILD_TYPE=$BUILD_TYPE -o ./artifacts
