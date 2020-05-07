#!/usr/bin/env python3
"""
This script takes data files from Wildfire, and make them into a Stracciatella mod.

The script expects the presence of all required SLF files, and the destination
directory to be clean.
"""

import argparse
import os
import traceback
import sys
import colorama
from colorama import Fore, Back, Style
from fs.mountfs import MountFS
from fs.osfs import OSFS
from pathlib import Path

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
    ("NPCData", "093.npc"),
    ("NPCData", "117.npc"),
]

FILES_TO_EXCLUDE = [
    "Maps/i6.dat",
    "Tilesets/0/smguns.sti",
    "Tilesets/0/SMITEMS.STI",
    "Tilesets/0/smp1items.sti",
    "Tilesets/0/smp2items.sti",
    "Tilesets/0/SMP3ITEMS.STI",
]

is_verbose = False

OK_LABEL    = Fore.GREEN + Style.BRIGHT + '[OK]' + Style.RESET_ALL
WARN_LABEL  = Fore.YELLOW + Style.BRIGHT + '[WARN]' + Style.RESET_ALL
ERROR_LABEL = Fore.RED + Style.BRIGHT + '[ERROR]' + Style.RESET_ALL

def main():
    global is_verbose
    colorama.init()

    """Checking the installation environment, and installs if OK"""
    parser = argparse.ArgumentParser(description='Install Wildfire mod')
    parser.add_argument(
        '--work_dir', help="path to the mod's Data directory", default='./Data', required=False
    )
    parser.add_argument(
        '--src_dir', help="path to the source Wildfire data directory", default='', required=False
    )
    parser.add_argument(
        '--verbose', help='display detailed error messages', action='store_true'
    )
    args = parser.parse_args()

    is_verbose = args.verbose
    work_dir = Path(args.work_dir)
    src_dir = determine_src_path(args.src_dir)

    preflight_checks(src_dir, work_dir)

    for slf in DIRS_TO_UNPACK:
        unpack_slf(src_dir, work_dir, slf)

    for slf, res in FILES_TO_EXTRACT:
        extract_single_resource(src_dir, work_dir, slf, res)

    for f in FILES_TO_EXCLUDE:
        delete_file(work_dir, f)

    convert_bmap(work_dir)
    replace_maps(work_dir)

    print(Fore.GREEN + "Installation finished" + Style.RESET_ALL)
    if os.name == 'nt':
        input("\nPress enter to close...")


def determine_src_path(src_dir):
    if src_dir:
        # given in command args
        return Path(src_dir)

    try:
        # not given, try opening a prompt dialog
        from tkinter import Tk
        from tkinter.filedialog import askdirectory
        tk = Tk()
        dir = askdirectory(title='Select Wildfare data folder', mustexist =True)
        tk.destroy()
        if dir:
            return Path(dir)
    except:
        # ignore errors, maybe there is no display
        pass

    print("You must provide the Wildfire source data directory.")
    sys.exit(1)


def preflight_checks(src_path, work_path):
    """Check we have all the data resource files are present in the right place"""
    has_errors = False
    print("Using " + str(src_path.resolve()) + " as source directory.")
    print("Checking for data files...")

    required_slf_files = DIRS_TO_UNPACK + list(map(lambda t: t[0], FILES_TO_EXTRACT))
    required_slf_files = set(required_slf_files)

    if not (work_path).is_dir():
        raise RuntimeError("Destination Data/ directory does not exist. You should run the installer from the mod directory")

    for slf in required_slf_files:
        file_name = slf + ".slf"
        if (src_path / file_name).is_file():
            print("  * %s %s exists" % (OK_LABEL, file_name))
        else:
            has_errors = True
            print("  * %s %s does not exist in %s" % (ERROR_LABEL, file_name, str(src_path.resolve())))
        if (work_path / slf).is_dir():
            print("  * %s Destination directory %s/ already exists" % (WARN_LABEL, slf))

    if has_errors:
        raise RuntimeError("Some data files or directories are missing. Please check the README and make sure you" +
            " have all the required data files.")
    else:
        print("Pre-flight checks OK... Proceeding to installation")


def unpack_slf(src_path, work_path, slf_name):
    """Unpacks the entire SLF file at the current directory"""
    combined_fs = open_slf_for_copy(src_path, work_path, slf_name)

    print("  * Unpacking " + slf_name)
    combined_fs.copydir('/slf', '/out', overwrite=True)
    combined_fs.close()


def delete_file(work_path, file_path):
    """We are only interested in maps, delete any other un-needed files."""
    print("  * Deleting " + file_path)
    (work_path / file_path).unlink()


def extract_single_resource(src_path, work_path, slf_name, resource_path):
    """Extracts a single resource file from the SLF"""
    combined_fs = open_slf_for_copy(src_path, work_path, slf_name)

    print("  * Extracting " + slf_name + "/" + resource_path)
    combined_fs.copy('/slf/' + resource_path, '/out/' + resource_path, overwrite=True)
    combined_fs.close()


def open_slf_for_copy(src_path, dest_path, slf_name):
    """Opens an SLF files for reading and returns a MountFS"""
    slf_file = src_path / (slf_name + ".slf")
    slf_fs = SlfFS(str(slf_file))

    output_dir = dest_path / slf_name
    output_dir.mkdir(exist_ok=True)
    out_fs = OSFS(output_dir)

    combined_fs = MountFS()
    combined_fs.mountdir('slf', slf_fs)
    combined_fs.mountdir('out', out_fs)

    return combined_fs


def convert_bmap(work_path):
    """Converts the bmap.sti in Wildfire to bmap.pcx which is needed by Vanilla/JA2:S"""
    sti_file = work_path / "InterFace" / "b_map.sti"
    output_file = work_path / "InterFace" / "b_map.pcx"

    print("  * Converting InterFace/b_map.{sti => pcx}")
    with open(sti_file, 'rb') as file:
        sti = load_16bit_sti(file)
        image = sti.image.convert("P", colors=8)
        image.save(output_file)


def replace_maps(work_path):
    """Work-around some known issues with certain sectors."""
    # We want the alternate map for G6, but no logic in Vanilla codebase to switch
    print("  * Replacing G6.dat with alternate")
    (work_path / "Maps" / "g6_a.dat").replace(work_path / "Maps" / "g6.dat")        


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print("\n" + Fore.RED + str(e) + Fore.RESET)
        if is_verbose:
            print(Style.DIM + Fore.BLUE + "\nError traceback:\n")
            traceback.print_exc()
            print(Style.RESET_ALL)
        print("\nInstallation aborted with an error.")
        if os.name == 'nt':
            input("\nPress enter to close...")

        exit(1)

