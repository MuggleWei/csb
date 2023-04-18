#!/bin/bash

origin_dir="$(dirname "$(readlink -f "$0")")"
cd $origin_dir

./pyinstaller_pkg.sh

mkdir -p ~/.local/bin
cp dist/hpb/hpb ~/.local/bin/

mkdir -p ~/.hpb
cp -r dist/hpb/etc/settings.xml ~/.hpb/
cp -r dist/hpb/share ~/.hpb/
