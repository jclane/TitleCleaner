#!/usr/bin/env python3

import argparse
from os import walk as oswalk
from os import makedirs as osmakedirs
from os.path import join as ospathjoin
from os.path import isdir as osisdir
from os.path import isfile as osisfile
from os.path import splitext as ossplitext
from os.path import exists as osexists
from os.path import dirname as osdirname
from shutil import copy2

from classes import Movie as Movie
from classes import Series as Series


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


def process_filenames(files, vid_type, output_dir):
    """
    Takes a list of files and passes their names to confirmTitle
    to try and get the actual movie title before copying the file
    to a the 'clean_titles' directory.  Creating said directory
    if necessary.

    :param files: List of files to check
    :param vid_type: Either "movies" or "series"
    """
    osmakedirs(output_dir, exist_ok=True)
    for file in files:
        vid_type = file.split("/")[1].lower()
        vid_obj = Series(file) if vid_type.lower() == "tv" else Movie(file) # This will have to be changed later to grab the torrent files as they finish
        new_path = ospathjoin(output_dir, vid_obj.path)
        if not osisdir(osdirname(new_path)):
            osmakedirs(osdirname(new_path), exist_ok=True)
        copy2(file, new_path)


def check_type(type_arg):
    if type_arg.lower() in ("movie", "series"):
        return "Movie" if type_arg.lower() == "movie" else "Series"
    else:
        raise argparse.ArgumentTypeError("Type should be either 'movie' or 'series'.")


def check_input_path(input_arg):
    if osexists(input_arg):
        return input_arg
    else:
        raise argparse.ArgumentTypeError("Supplied input path is not valid.  No such file or directory.\n" + input_arg)

parser = argparse.ArgumentParser(prog="TitleCleaner",
                                 description='Clean up torrented video file names.')
parser.add_argument("-r", "-R", "--recursive", dest="recursive", action="store_true",
                    help="clean video file names recursively")
parser.add_argument("-t, --type", dest="vid_type", type=check_type, help="type of video ('Movie' or 'Series')")
parser.add_argument("input_path", type=check_input_path, help="path to file or folder to clean")
parser.add_argument("output_path", type=str, help="path to folder to save cleaned files")
args = parser.parse_args()

if args.recursive:
    if osisdir(args.input_path):
        files = get_filenames(args.input_path)
        process_filenames(files, args.vid_type, args.output_path)
    else:
        parser.error("The rescursive flag is set, but the supplied input points to a file.")
else:
    if osisdir(args.input_path):
        parser.error("The rescursive flag is not set, but the supplied input points to a directory.")
    if osisfile(args.input_path) and ossplitext(args.input_path)[1] in (".mkv", ".mp4"):
        process_filenames([args.input_path], args.vid_type, args.output_path)
    else:
        parser.error("If recursive flag is set then the input path must point to a video file.")
