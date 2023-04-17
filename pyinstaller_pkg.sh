#!/bin/bash

origin_dir="$(dirname "$(readlink -f "$0")")"
cd $origin_dir

if [ -d "venv" ]; then
	echo "venv already exists"
else
	echo "create venv"
	python -m venv venv
fi

source venv/bin/activate

if [ $? -eq 0 ]; then
	echo "success source activate"
else
	echo "failed source activate"
	exit 1
fi

pip install -r requirements.dev.txt

pyinstaller -F hpb/main.py --distpath dist/hpb -n hpb
cp -r ./hpb/etc dist/hpb/
cp -r ./share dist/hpb/
cp ./README.md dist/hpb/
cp ./README_cn.md dist/hpb/
