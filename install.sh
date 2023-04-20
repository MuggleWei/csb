#!/bin/bash

origin_dir="$(dirname "$(readlink -f "$0")")"
cd $origin_dir

python -m pip install --user -e .

mkdir -p ~/.hpb
cp -r ./etc/settings.xml ~/.hpb/
cp -r ./share ~/.hpb/
