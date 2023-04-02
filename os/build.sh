#!/bin/bash

# handle argv
if [ "$#" -lt 2 ]; then
	echo "[ERROR] Usage: $0 <OS> <OS_VER> [mirror]"
	echo "    @param OS: alpine, ubuntu, etc..."
	echo "    @param OS_VER: os version"
	echo "    @param mirror: mirror address"
	echo "e.g."
	echo "    $0 alpine 3.17"
	echo "    $0 ubuntu 22.04"
	echo "    $0 alpine 3.17 mirrors.tuna.tsinghua.edu.cn"
	echo "    $0 ubuntu 22.04 mirrors.ustc.edu.cn"
	exit 1
else
	OS=$1
	OS_VER=$2
	if [[ $# -gt 2 ]]; then
		MIRROR=$3
		echo "mirror be set: $MIRROR"
	else
		MIRROR=
	fi
fi

origin_dir=$(readlink -f "$(dirname "$0")")
cd $origin_dir

REGISTRY=csb
img_name="${REGISTRY}/${OS}:${OS_VER}"
echo "build image: ${img_name}"

docker build \
	--build-arg OS_VER=$OS_VER \
	--build-arg MIRROR=$MIRROR \
	-f ./${OS}.Dockerfile \
	-t ${img_name} \
	.
