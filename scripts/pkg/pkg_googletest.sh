#!/bin/bash

if [ "$#" -lt 1 ]; then
	echo "Usage: $0 <Debug|Release>"
	echo "build without specify build type, use release by default"
	BUILD_TYPE=release
else
	# to lowercase
	BUILD_TYPE=$(echo $1 | tr '[:upper:]' '[:lower:]')
fi

hpb build \
	-c etc/metas/googletest/googletest.yml \
	-p git_tag=v1.13.0 \
	-p build_type=$BUILD_TYPE \
	-o ./artifacts
