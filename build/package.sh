#!/bin/bash

rm *.spec
pyinstaller ../src/install_wildfire_maps.py \
    --distpath ../dist \
    --paths ../lib/ja2-open-toolset \
    --onefile

pushd ..
rm -rf dist/wildfire-maps/
mkdir -p dist/wildfire-maps
mv dist/install_wildfire_maps dist/wildfire-maps/
cp -R assets/wildfire-maps/ dist/
cp README.txt KNOWN_ISSUES.txt  dist/wildfire-maps/

pushd dist
tar zcf wildfire-maps.tar.gz wildfire-maps/
