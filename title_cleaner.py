#!/usr/bin/python3.7

import argparse
from os import walk as oswalk
from os import makedirs as osmakedirs
from os.path import join as ospathjoin
from os.path import isdir as osisdir
from os.path import splitext as ossplitext
from shutil import copy2

from classes import Movie as Movie
from classes import Series as Series


## WORKING!
def get_filenames(root_dir):
    """
    Walks 'root_dir' in order to obtain a list of *.mkv/*.mp4 files.

    :param root_dir: Root directory to walk
    :param vid_type: Either 'movies' or 'tv'
    :return: Either a list of files or an error message
    """

    videos = []
    for main_dir, sub_dirs, files in oswalk(root_dir):
        for file in files:
            if ossplitext(file)[1] in (".mkv", ".mp4"):
                videos.append(ospathjoin(main_dir, file))
    if len(videos) > 0:
        return videos
    else:
        return "ERR: No video files found!"

def process_filename(filename, vid_type):
    pass


def process_filenames(files, vid_type, output_dir):
    """
    Takes a list of files and passes their names to confirmTitle
    to try and get the actual movie title before copying the file
    to a the 'clean_titles' directory.  Creating said directory
    if necessary.

    :param files: List of files to check
    :param vid_type: Either "movie" or "series"
    """

    if vid_type.lower() in ("movie", "series"):
        sub_dir = r"TV/" if vid_type.lower() == "series" else r"Movies/"
    else:
        print("ERR: Video type must either be 'movie' or 'series'!")

    print("\n"*5)
    osmakedirs(ospathjoin(output_dir, sub_dir), exist_ok=True)
    for file in files:
        if vid_type == "movie":
            vid_obj = Movie(file)
        else:
            vid_obj = Series(file)

        new_path = ospathjoin(output_dir, sub_dir, vid_obj.path, vid_obj.file_name)
        if osisdir(new_path):
            copy2(file, new_path)
        elif not osisdir(new_path):
            osmakedirs(new_path, exist_ok=True)
            copy2(file, new_path)


parser = argparse.ArgumentParser(prog="TitleCleaner",
                                 description='Clean up torrented video file names.')
parser.add_argument("-D", "--dir", dest="dir", action="store_true",
                    help="Walk through directories.")
parser.add_argument("type", nargs="?", help="Type of video.  Either 'Movie' or 'Series'.")
parser.add_argument("-i", "--in", dest="INPUT", required=True, help="Path to file or folder to clean.")
parser.add_argument("-o", "--out", dest="OUTPUT", required=True, help="Path to file or folder to save cleaned files.")

args = parser.parse_args()

if args.dir:
    print(args)
    print(args.INPUT)
    print(args.OUTPUT)
    files = get_filenames(args.INPUT)
    print(files)
    process_filenames(files, args.type, args.OUTPUT)


