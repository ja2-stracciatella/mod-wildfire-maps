#!/bin/bash
# This is packaging script assumes an environment like TravisCI.

OS=${TRAVIS_OS_NAME-unknown}
TAG=${TRAVIS_TAG-untagged}

BASE_DIR="$(dirname "$BASH_SOURCE")/.."
DIST_DIR="$BASE_DIR/dist/wildfire-maps"

# Create executable binary
pyinstaller $BASE_DIR/src/install_wildfire_maps.py \
    --distpath $BASE_DIR/dist/ \
    --paths $BASE_DIR/lib/ja2-open-toolset \
    --onefile

# Create dist package
rm    -rf $DIST_DIR/
mkdir -p  $DIST_DIR/
mv    $BASE_DIR/dist/install_wildfire_maps*            $DIST_DIR/
cp -R $BASE_DIR/assets/wildfire-maps/*                 $DIST_DIR/
cp    $BASE_DIR/README.md $BASE_DIR/KNOWN_ISSUES.md    $DIST_DIR/

pushd $BASE_DIR/dist
if [ "$OS" = "windows" ]; then
    7z  a   wildfire-maps_${TAG}-${OS}.zip    wildfire-maps/
else
    tar zcf wildfire-maps_${TAG}-${OS}.tar.gz wildfire-maps/
fi
popd
