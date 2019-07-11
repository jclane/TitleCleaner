#!/usr/bin/python3.7

import requests
import re
from os import environ
from os import walk as oswalk
from os import makedirs as osmakedirs
from os.path import join as ospathjoin
from os.path import isdir as osisdir
from os.path import split as ossplit
from os.path import splitext as ossplitext
from fuzzywuzzy import process as fuzzyprocess
import tvdbsimple as tvdb
#from os.path import dirname as osdirname
#from os.path import basename as osbasename
from shutil import copy2


tvshows = r"testing/TV/"
movies = r"testing/Movies/"

class Video:
    def __init__(self, full_path, vid_type):
        self.file_name = ossplit(full_path)[1]
        self.file_ext = ossplitext(self.file_name)[1]
        self.year = self.parse_year(full_path)
        self.title = ossplitext(ossplit(full_path)[1])[0]
        self.path = ossplit(full_path)[0]
        self.vid_type = vid_type

    def set_title(self, title):
        self.title = title

    def get_path(self):
        return self.path

    def parse_year(self, file_name):
        """Returns what I hope a year from 'file_name' else returns boolean False.
        """
        year = re.search(r"(\d{4}(?![a-zA-Z]))", file_name)
        if year is not None:
            return year.group(1)
        else:
            return False

    def remove_common_strings(self, file_name):
        """
        Removes common strings from "file_name" such as
        DVDrip, 1080p, x264 and so on.
        """
        common_strings = ["DVDRIP", "BLURAY", "1080P", "1080",
                          "720", "720P", "X264", "SD", "HD",
                          "HDTV", "WEB", "AMZN", "DIVX", "DD51",
                          "AVC"]
        name_arr = file_name.split(".")
        if self.year:
            name_arr.remove(self.year)
        filtered = list(filter(lambda el: el.upper() not in common_strings, name_arr))
        distilled = []
        for el in filtered:
            for ndex in range(0, len(common_strings)):
                if el in common_strings[ndex] or common_strings[ndex] in el:
                    break
                if common_strings[ndex] == common_strings[-1]:
                    distilled.append(el)
        return " ".join(distilled)

    def match_title(self, titles):
        return fuzzyprocess.extractOne(self.title, titles)[0]

    def call_omdb(self):
        api = "http://www.omdbapi.com/?apikey={}&s={}&y={}&type={}".format(environ["OMDBKEY"], self.title, self.year, self.vid_type)
        req = requests.get(api)
        if req.status_code == requests.codes.ok:
            json = req.json()
            if json["Response"] == "True":
                return [result["Title"]for result in json["Search"]]
            if json["Response"] == "False":
                return "TITLE NOT FOUND"
        else:
            print(req.status_code)

## NEED BETTER WAY TO MATCH MOVIES!!  ONE WRONG CHAR AND FAILS!!
class Movie(Video):
    def __init__(self, full_path, vid_type="movie"):
        super().__init__(full_path, vid_type)
        self.title = self.remove_common_strings(self.title.replace(self.file_ext, ""))
        print(self.title)
        self.year = self.parse_year(full_path)
        self.set_title(self.match_title(self.call_omdb()))
        self.set_file_name()
        self.set_path()

    def set_file_name(self):
        file_name = [self.title]
        if self.year:
            file_name.append("({})".format(self.year))
        self.file_name = " ".join(file_name) + ossplitext(self.file_name)[1]

    def set_path(self):
        folder_name = [self.title]
        if self.year:
            folder_name.append("({})".format(self.year))
        self.path = ospathjoin(" ".join(folder_name), self.file_name)

## WORKING!
class Series(Video):
    def __init__(self, full_path, vid_type="series"):
        super().__init__(full_path, vid_type)
        self.season = self.parse_season_num(self.file_name)
        self.episode = self.parse_episode_num(self.file_name)
        self.set_title(self.cross_check_title())
        self.set_file_name(self.file_name)
        self.set_path()

    def set_file_name(self, ext):
        file_name = [self.title]
        if self.year:
            file_name.append("({})".format(self.year))
        if self.season:
            file_name.append("S{}:E{}".format(self.season, self.episode))
        else:
            file_name.append("Episode {}".format(self.episode))
        self.file_name = " - ".join(file_name) + self.file_ext

    def set_path(self):
        series_folder = self.title
        if self.year:
            series_folder += " ({})".format(self.year)
        if self.season:
            season_folder = "Season {}".format(self.season)
            self.path = ospathjoin(series_folder, season_folder, self.file_name)
        else:
            self.path = ospathjoin(series_folder, self.file_name)

    def parse_season_num(self, file_name):
        # The regex looks for 1 to 2 digits preceeded by 's' or 'season' OR
        # followed by 'x'
        # original REGEX = r"(?<=s)\d{2}|(?<=season)\s*\d{,2}|\d{,2}(?=x)", re.I
        regex = re.compile(r"s\d{2}|season\s*\d{,2}|\d{,2}x", re.I)
        match = regex.search(file_name)
        if match is not None:
            start_ndex = file_name.index(match.group())
            self.set_title(" ".join(self.title[:start_ndex - 1].split(".")))  # This will only work if 'season' is in 'file_name'
            return re.sub('[^0-9]','', match.group())
        else:
            return False

    def parse_episode_num(self, file_name):
        # original REGEX = r"(?ix)(?:e|x|episode|^)\s*(\d{2})", re.I
        regex = re.compile(r"(?ix)(?:e|x|episode|^)\s*(\d{2})", re.I)
        match = regex.search(file_name)
        if match is not None:
            start_ndex = file_name.index(match.group())
            self.set_title(" ".join(self.title[:start_ndex - 1].split(".")))  # This will only work if 'episode' is in 'file_name'
            return re.sub('[^0-9]','', match.group())
        else:
            return False

    def call_tvdb(self):
        tvdb.KEYS.API_KEY = environ["TVDBKEY"]
        results = []
        search = tvdb.Search()
        response = search.series(self.title)
        for r in response:
            if self.year:
                if self.year in r["firstAired"]:
                    results.append(r["seriesName"])
            else:
                results.append(r["seriesName"])
        return results

    def cross_check_title(self):
        results = self.call_tvdb()
        results += self.call_omdb()
        return self.match_title(results)


def buildNewPath(file_name, vid_type):
    clean_title = removeCommonStrings(file_name)

    if vid_type == "series":
        season_and_episode = getSeasonAndEpisode(clean_title)
        clean_title = clean_title.lower().replace(season_and_episode + ".", "")

    year = getYear(clean_title)
    if year:
        clean_title.replase(year, "")

    clean_title_lst = clean_title.split(".")

    for num in range(0, len(clean_title_lst)):
        result = getTitle(clean_title_lst[num:], year, vid_type)
        if result[1]:
            if year:
                new_file_name = "{} {} - {}".format(result[0], "("+year+")", season_and_episode)

            else:
                new_file_name = "{} - {}".format(result[0], season_and_episode)

    for num in range(len(clean_title_lst), 0, -1):
        result = getTitle(clean_title_lst[:num], year, vid_type)
        if result[1]:
            if year:
                new_file_name = "{} {} - {}".format(result[0], "("+year+")", season_and_episode)
            else:
                new_file_name = "{} - {}".format(result[0], season_and_episode)
        if not result[1] and num == 0:
            print("end of the line")
            print(clean_title_lst, result)
            return file_name

## WORKING!
def getFiles(root_dir, vid_type):
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


def processFiles(files, vid_type):
    """
    Takes a list of files and passes their names to confirmTitle
    to try and get the actual movie title before copying the file
    to a the 'clean_titles' directory.  Creating said directory
    if necessary.

    :param files: List of files to check
    :param vid_type: Either "movie" or "series"
    """

    if vid_type in ("movie", "series"):
        root_dir = r"TV/" if vid_type == "series" else r"Movies/"
    else:
        print("ERR: Video type must either be 'movie' or 'series'!")

    osmakedirs(r"testing/clean_titles/" + root_dir, exist_ok=True)
    for file in files:
        if vid_type == "movie":
            vid_obj = Movie(file)
        else:
            vid_obj = Series(file)

        new_path = ospathjoin(r"testing/clean_titles/", root_dir, vid_obj.path, vid_obj.file_name)
        if osisdir(new_path):
            copy2(file, new_path)
        elif not osisdir(new_path):
            osmakedirs(new_path, exist_ok=True)
            copy2(file, new_path)

files = getFiles(tvshows, "series")
processFiles(files, "series")
