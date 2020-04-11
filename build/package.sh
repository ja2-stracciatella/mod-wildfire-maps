#!/bin/bash
pyinstaller ../src/install_wildfire_maps.py \
    --distpath ../dist \
    --paths ../lib/ja2-open-toolset \
    --onefile --console