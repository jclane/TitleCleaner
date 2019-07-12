import requests
import re
from os import environ
from os.path import split as ossplit
from os.path import join as ospathjoin
from os.path import splitext as ossplitext
from fuzzywuzzy import process as fuzzyprocess
import tvdbsimple as tvdb

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
