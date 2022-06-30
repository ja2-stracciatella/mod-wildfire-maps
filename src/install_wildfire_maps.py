#!/usr/bin/env python3
"""
This script takes data files from Wildfire, and make them into a Stracciatella mod.

The script expects the presence of all required SLF files, and the destination
directory to be clean.
"""

import argparse
import colorama
import os
import traceback
import sys
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
    "JA2set.dat",
    "MilitiaMaps.sti",
    "b_map.sti",
    "069.npc", # VINCE
    "080.npc", # STEVE
    "093.npc", # SPIKE
    "117.npc", # HANS
    "132.npc", # JENNY
]

FILES_TO_EXCLUDE = [
    "Tilesets/0/smguns.sti",
    "Tilesets/0/SMITEMS.STI",
    "Tilesets/0/smp1items.sti",
    "Tilesets/0/smp2items.sti",
    "Tilesets/0/SMP3ITEMS.STI",
]

is_verbose = False

OK_LABEL    = Fore.GREEN  + Style.BRIGHT + '[OK]'    + Style.RESET_ALL
WARN_LABEL  = Fore.YELLOW + Style.BRIGHT + '[WARN]'  + Style.RESET_ALL
ERROR_LABEL = Fore.RED    + Style.BRIGHT + '[ERROR]' + Style.RESET_ALL

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

    for res in FILES_TO_EXTRACT:
        extract_single_resource(src_dir, work_dir, res)

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
        dir = askdirectory(title='Select Wildfire data folder', mustexist =True)
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

    required_slf_files = DIRS_TO_UNPACK
    required_slf_files = set(required_slf_files)

    if not (work_path).is_dir():
        raise RuntimeError("Destination Data/ directory does not exist. You should run the installer from the mod directory")

    for slf in required_slf_files:
        file_name = slf + ".slf"
        file_name = resolve_case_insensitive_path(src_path, file_name)
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
    file_path = resolve_case_insensitive_path(work_path, file_path)
    print("  * Deleting " + str(file_path))
    (work_path / file_path).unlink()


def extract_single_resource(src_path, work_path, resource_path):
    """Extracts a single resource file from any SLF in the source path"""
    slf_name, resource_path = find_slf_that_contains_resource(src_path, resource_path)
    if slf_name is None or resource_path is None:
        raise RuntimeError("Could not find SLF file that contains " + resource_path)
    combined_fs = open_slf_for_copy(src_path, work_path, slf_name)

    print("  * Extracting " + slf_name + "/" + resource_path)
    combined_fs.copy('/slf/' + resource_path, '/out/' + resource_path, overwrite=True)
    combined_fs.close()


def find_slf_that_contains_resource(src_path, resource_path):
    """Finds the SLF that contains a resource_path and returns case sensitive slf file name and resource path"""
    slf_files = [f for f in os.listdir(src_path) if os.path.isfile(src_path / f) and f.lower().endswith(".slf")]
    for slf_filename in slf_files:
        slf_fs = SlfFS(str(src_path / slf_filename))
        for r in slf_fs.listdir("/"):
            if r.lower() == resource_path.lower():
                return slf_filename[:-4], r
    return None, None

def open_slf_for_copy(src_path, dest_path, slf_name):
    """Opens an SLF files for reading and returns a MountFS"""
    slf_filename = resolve_case_insensitive_path(src_path, slf_name + ".slf")
    slf_file = src_path / slf_filename
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
    interface_dir = resolve_case_insensitive_path(work_path, "Interface")
    sti_filename = resolve_case_insensitive_path(work_path / interface_dir, "b_map.sti")
    sti_file = work_path / interface_dir / sti_filename
    output_file = work_path / interface_dir / "b_map.pcx"

    print("  * Converting InterFace/b_map.{sti => pcx}")
    with open(sti_file, 'rb') as file:
        sti = load_16bit_sti(file)
        image = sti.image.convert("P", colors=8)
        image.save(output_file)


def replace_maps(work_path):
    """Work-around some known issues with certain sectors."""
    # We want the alternate map for G6, but no logic in Vanilla codebase to switch
    print("  * Replacing G6.dat with alternate")
    maps_dir = resolve_case_insensitive_path(work_path, "maps")
    map_filename = resolve_case_insensitive_path(work_path / maps_dir, "g6_a.dat")
    (work_path / maps_dir / map_filename).replace(work_path / maps_dir / "g6.dat")

def resolve_case_insensitive_path(directory, path):
    parts = Path(path).parts
    current = directory
    path = ""
    for p in parts:
        listing = os.listdir(current)
        found = False
        for l in listing:
            if p.lower() == l.lower():
                current = os.path.join(current, l)
                path = os.path.join(path, l)
                found = True
                break;
        if not found:
            current = os.path.join(current, p)
            path = os.path.join(path, p)
    return Path(path)

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

