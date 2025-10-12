#!/bin/bash
# This is packaging script assumes an environment like TravisCI.

OS=${CI_OS_NAME-unknown}
TAG=${CI_GIT_TAG-untagged}

BASE_DIR="$(dirname "$BASH_SOURCE")/.."
DIST_DIR="$BASE_DIR/dist/wildfire-maps"

pyinstaller $BASE_DIR/src/install_wildfire_maps.py \
    --hidden-import='pkg_resources.py2_warn' \
    --distpath $BASE_DIR/dist/ \
    --hidden-import='PIL._imaging' \
    --collect-all='PIL' \
    --onefile

# # Create executable binary
# if [ "$OS" = "windows" ]; then
#     # Use spec file for Windows to handle PIL dependencies better
#     pyinstaller $BASE_DIR/build/install_wildfire_maps.spec \
#         --distpath $BASE_DIR/dist/ \
#         --workpath $BASE_DIR/build/work \
#         --specpath $BASE_DIR/build
# else
#     # Use command line for other platforms
#     pyinstaller $BASE_DIR/src/install_wildfire_maps.py \
#         --hidden-import='pkg_resources.py2_warn' \
#         --hidden-import='PIL._imaging' \
#         --hidden-import='PIL._imagingmorph' \
#         --hidden-import='PIL._imagingft' \
#         --hidden-import='PIL._imagingmath' \
#         --hidden-import='PIL._imagingcms' \
#         --collect-all='PIL' \
#         --distpath $BASE_DIR/dist/ \
#         --paths $BASE_DIR/lib/ja2-open-toolset \
#         --onefile
# fi

# # Windows fallback: If the spec file approach fails, try with explicit DLL collection
# if [ "$OS" = "windows" ] && [ ! -f "$BASE_DIR/dist/install_wildfire_maps.exe" ]; then
#     echo "Spec file approach failed, trying fallback method..."
#     pyinstaller $BASE_DIR/src/install_wildfire_maps.py \
#         --hidden-import='pkg_resources.py2_warn' \
#         --hidden-import='PIL._imaging' \
#         --hidden-import='PIL._imagingmorph' \
#         --hidden-import='PIL._imagingft' \
#         --hidden-import='PIL._imagingmath' \
#         --hidden-import='PIL._imagingcms' \
#         --collect-all='PIL' \
#         --collect-binaries='PIL' \
#         --collect-data='PIL' \
#         --distpath $BASE_DIR/dist/ \
#         --paths $BASE_DIR/lib/ja2-open-toolset \
#         --onefile
# fi

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
