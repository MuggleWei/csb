#!/bin/bash

if [ "$#" -lt 1 ]; then
	echo "Usage: $0 <Debug|Release>"
	echo "build without specify build type, use release by default"
	BUILD_TYPE=release
else
	# to lowercase
	BUILD_TYPE=$(echo $1 | tr '[:upper:]' '[:lower:]')
fi

GIT_TAG=v1.13.0
REGISTRY=hpb
OUTPUT_DIR=artifacts
SOURCE_DIR=artifacts/src

mkdir -p ${SOURCE_DIR}
if [ ! -d ${SOURCE_DIR}/googletest ]; then
	git clone \
		--depth=1 \
		--branch=${GIT_TAG} \
		https://github.com/google/googletest.git \
		${SOURCE_DIR}/googletest
fi

hpb build \
	-c etc/metas/googletest/googletest.docker.yml \
	-p SOURCE_DIR=${SOURCE_DIR} \
	-p GIT_TAG=${GIT_TAG} \
	-p BUILD_TYPE=${BUILD_TYPE} \
	-p REGISTRY=${REGISTRY} \
	-p OS=ubuntu \
	-p OS_VER=22.04 \
	-o ${OUTPUT_DIR}

hpb build \
	-c etc/metas/googletest/googletest.docker.yml \
	-p SOURCE_DIR=${SOURCE_DIR} \
	-p GIT_TAG=${GIT_TAG} \
	-p BUILD_TYPE=${BUILD_TYPE} \
	-p REGISTRY=${REGISTRY} \
	-p OS=alpine \
	-p OS_VER=3.17 \
	-o ${OUTPUT_DIR}
