#!/bin/bash

origin_dir="$(dirname "$(readlink -f "$0")")"
cd $origin_dir

echo "# start install hpb"
python -m pip install --user .

mkdir -p ~/.hpb
echo "# copy etc/settings.xml -> ~/.hpb/"
cp -r ./etc/settings.xml ~/.hpb/
echo "# copy share -> ~/.hpb/"
cp -r ./share ~/.hpb/
