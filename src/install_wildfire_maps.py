#!/usr/bin/env python3
"""
This script takes data files from Wildfire, and make them into a Stracciatella mod.

The script expects the presence of all required SLF files, and the destination
directory to be clean.
"""

import argparse
import os
import shutil
import traceback
from pathlib import Path
from fs.mountfs import MountFS
from fs.osfs import OSFS

from ja2py.fileformats import SlfFS
from ja2py.fileformats.Sti import load_16bit_sti


DIRS_TO_UNPACK = [
    "Maps",
    "RadarMaps",
    "TileSets"
]

FILES_TO_EXTRACT = [
    ("BinaryData", "JA2set.dat"),
    ("InterFace", "MilitiaMaps.sti"),
    ("InterFace", "b_map.sti"),
    ("NPCData", "059.npc")
]


def main():
    """Checking the installation environment, and installs if OK"""
    parser = argparse.ArgumentParser(description='Install Wildfire mod')
    parser.add_argument(
        '--work_dir', help="path to the Data directory", default='./Data', required=False
    )
    args = parser.parse_args()

    work_dir = Path(args.work_dir)
    preflight_checks(work_dir)

    for slf in DIRS_TO_UNPACK:
        unpack_slf(work_dir, slf)

    for slf, res in FILES_TO_EXTRACT:
        extract_single_resource(work_dir, slf, res)

    convert_bmap(work_dir)
    move_unusable_maps(work_dir)
    move_slf_away(work_dir)

    print("Installation finished")
    if os.name == 'nt':
        input("\nPress enter to close...")


def preflight_checks(work_path):
    """Check we have all the data resource files are present in the right place"""
    has_errors = False
    print("Checking data files in " + str(work_path.resolve()) + "...")

    required_slf_files = DIRS_TO_UNPACK + list(map(lambda t: t[0], FILES_TO_EXTRACT))
    required_slf_files = set(required_slf_files)
    for slf in required_slf_files:
        file_name = slf + ".slf"
        if (work_path / file_name).is_file():
            print("  * [OK] " + file_name + " exists")
        else:
            has_errors = True
            print("  * [ERROR] " +  file_name + " does not exist in " + str(work_path.resolve()))
        if (work_path / slf).is_dir():
            print("  * [WARN] Destination directory " + slf + "/ already exists")
                
    if has_errors:
        raise RuntimeError("Some data files are missing. Please check the README and make sure you" +
            " have all the required data files.")
    else:
        print("Pre-flight checks OK... Proceeding to installation")


def unpack_slf(work_path, slf_name):
    """Unpacks the entire SLF file at the current directory"""
    combined_fs = open_slf_for_copy(work_path, slf_name)

    print("  * Unpacking " + slf_name)
    combined_fs.copydir('/slf', '/out', overwrite=True)
    combined_fs.close()


def extract_single_resource(work_path, slf_name, resource_path):
    """Extracts a single resource file from the SLF"""
    combined_fs = open_slf_for_copy(work_path, slf_name)

    print("  * Extracting " + slf_name + "/" + resource_path)
    combined_fs.copy('/slf/' + resource_path, '/out/' + resource_path, overwrite=True)
    combined_fs.close()


def open_slf_for_copy(work_path, slf_name):
    """Opens an SLF files for reading and returns a MountFS"""
    slf_file = work_path / (slf_name + ".slf")
    slf_fs = SlfFS(str(slf_file))

    output_dir = work_path / slf_name
    output_dir.mkdir(exist_ok=True)
    out_fs = OSFS(output_dir)

    combined_fs = MountFS()
    combined_fs.mountdir('slf', slf_fs)
    combined_fs.mountdir('out', out_fs)

    return combined_fs


def convert_bmap(work_path):
    """Converts the bmap.sti in Wildfire  to bmap.pcx which is needed by Vanilla/JA2S"""
    sti_file = work_path / "InterFace" / "b_map.sti"
    output_file = work_path / "InterFace" / "b_map.pcx"

    print("  * Converting InterFace/b_map.{sti => pcx}")
    with open(sti_file, 'rb') as file:
        sti = load_16bit_sti(file)
        image = sti.image.convert("P", colors=8)
        image.save(output_file)


def move_unusable_maps(work_path):
    """Some known issues with certain sectors. Moving them away for now"""
    print("  * Moving aside un-useable maps")
    unused_dir = work_path / "Maps" / "_UNUSED"
    unused_dir.mkdir(exist_ok=True)
    (work_path / "Maps" / "i6.dat").replace(work_path / "Maps" / "_UNUSED" / "i6.dat")
    (work_path / "Maps" / "g6.dat").replace(work_path / "Maps" / "_UNUSED" / "g6.dat")
    (work_path / "Maps" / "g6_a.dat").replace(work_path / "Maps" / "g6.dat")        


def move_slf_away(work_path):
    """Done with the installation. The SLF files are not read by JA2S. Move the SLF files away to avoid confusion"""
    print("  * Moving aside all SLF files")
    installed_dir = work_path / "_INSTALLED"
    installed_dir.mkdir(exist_ok=True)

    for f in work_path.glob("*.slf"):
        shutil.move(str(f), str(work_path / "_INSTALLED"))


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print()
        traceback.print_exc()
        if os.name == 'nt':
            input("\nPress enter to close...")
        exit(1)

