import requests
import re
from os import environ
from os.path import split as ossplit
from os.path import join as ospathjoin
from os.path import splitext as ossplitext
from time import sleep
from fuzzywuzzy import process as fuzzyprocess
import tvdbsimple as tvdb
import tmdbsimple as tmdb

class Video:
    def __init__(self, full_path, vid_type):
        self.file_name = ossplit(full_path)[1]
        self.file_ext = ossplitext(self.file_name)[1]
        self.title = ossplitext(ossplit(full_path)[1])[0]
        self.year = self.parse_year(full_path)
        self.path = ossplit(full_path)[0]
        self.vid_type = vid_type

    def set_title(self, title):
        self.title = title

    def parse_year(self, file_name):
        """Returns what I hope is the year from 'file_name' else returns boolean False.
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
                          "AVC", "REPACK", "RE-PACK", "XVID",
                          "HDCAM"]
        name_arr = file_name.split(".")
        if self.year:
            name_arr.remove(self.year)
        filtered = list(filter(lambda el: el.upper() not in common_strings, name_arr))
        distilled = []
        for el in filtered:
            for ndex in range(0, len(common_strings)):
                if el.upper() in common_strings[ndex] or common_strings[ndex] in el.upper():
                    break
                if common_strings[ndex] == common_strings[-1]:
                    distilled.append(el)
        return " ".join(distilled)

    def match_title(self, titles):
        """
        Uses 'fuzzyprocess' to find the closest match to 'self.title' in the
        list 'titles'.  If 'self.year' is not false and the match found includes
        it then it will be removed before being return.
        """
        match = fuzzyprocess.extractOne(self.title, titles)[0]
        if self.year and self.year in match:
            match = match.replace("(" + self.year + ")", "").strip()
        return match

    def call_omdb(self):
        api = "http://www.omdbapi.com/?apikey={}&s={}&y={}&type={}".format(environ["OMDBKEY"], self.title.strip(), self.year.strip() if self.year else "", self.vid_type)
        req = requests.get(api)
        results = []
        if req.status_code == requests.codes.ok:
            json = req.json()
            if json["Response"] == "True":
                results += [result["Title"]for result in json["Search"]]
        else:
            print(req.status_code)
        return results

    def call_tmdb(self):
        tmdb.API_KEY = environ["TMDBKEY"]
        search = tmdb.Search()
        response = search.movie(query=self.title)
        results = []
        if response["total_results"] == 0:
            title_arr = self.title.split()
            for ndex in range(len(title_arr), 0, -1):
                sleep(5)
                response = search.movie(query=" ".join(title_arr[:ndex]))
                if response["total_results"] > 0:
                    results += [result["title"] for result in response["results"]]
                    return results
        else:
            results += [result["title"] for result in response["results"]]
        return results


class Movie(Video):
    def __init__(self, full_path, vid_type="movie"):
        super().__init__(full_path, vid_type)
        self.title = self.remove_common_strings(self.title.replace(self.file_ext, ""))
        self.year = self.parse_year(full_path)
        self.set_title(self.cross_check_title())
        self.set_file_name()
        self.set_path()

    def cross_check_title(self):
        """
        This makes calls to the OMDB and TMDB APIs and stores the results
        of those calls the 'omdb' and 'tmdb' variables.  If the result is not
        an empty list it is added to the 'results' list and passed to 'match_title'.
        """
        omdb = self.call_omdb()
        tmdb = self.call_tmdb()
        results = []
        for call_result in [omdb, tmdb]:
            if len(call_result) > 0:
                results += call_result
        if len(results) > 0:
            return self.match_title(results)
        else:
            return self.title

    def set_file_name(self):
        file_name = [self.title]
        if self.year:
            file_name.append("({})".format(self.year))
        self.file_name = " ".join(file_name) + ossplitext(self.file_name)[1]

    def set_path(self):
        folder_name = r"Movies/" + self.title
        if self.year:
            folder_name += " ({})".format(self.year)
        self.path = ospathjoin(folder_name, self.file_name)


class Series(Video):
    def __init__(self, full_path, vid_type="series"):
        super().__init__(full_path, vid_type)
        self.title = self.remove_common_strings(self.title.replace(self.file_ext, ""))
        self.season = self.parse_season(self.title)
        self.episode = self.parse_episode(self.title)
        self.title = self.cross_check_titles()
        self.set_file_name(self.file_name)
        self.set_path()

    def set_file_name(self, ext):
        file_name = [self.title]
        if self.year:
            file_name[0] += (" ({})".format(self.year))
        if self.season:
            file_name.append("S{}:E{}".format(self.season, self.episode))
        else:
            file_name.append("Episode {}".format(self.episode))
        self.file_name = " - ".join(file_name) + self.file_ext

    def set_path(self):
        series_folder = r"TV/" + self.title
        if self.year:
            series_folder += " ({})".format(self.year)
        if self.season:
            season_folder = "Season {}".format(self.season)
            self.path = ospathjoin(series_folder, season_folder, self.file_name)
        else:
            self.path = ospathjoin(series_folder, self.file_name)

    def parse_season(self, file_name):
        # The regex looks for 1 to 2 digits preceeded by 's' or 'season' OR
        # followed by 'x'
        # original REGEX = r"(?<=s)\d{2}|(?<=season)\s*\d{,2}|\d{,2}(?=x)", re.I
        regex = re.compile(r"s\d{1,2}|season\s*\d{1,2}|\d{1,2}x\d{,2}", re.I)
        match = regex.search(file_name)
        if match is not None:
            self.set_title(self.title.replace(match.group(), "").strip())
            return "{:02d}".format(int(re.sub('[^0-9]','', match.group())))
        else:
            return False

    def parse_episode(self, file_name):
        # original REGEX = r"(?ix)(?:e|x|episode|^)\s*(\d{2})", re.I
        regex = re.compile(r"(?:x|e|episode)\d{1,2}", re.I)
        match = regex.search(file_name)
        if match is not None:
            start_ndex = file_name.index(match.group())
            self.set_title(" ".join(self.file_name[:start_ndex - 1].split(".")))  # This will only work if 'episode|e|x' is in 'file_name'
            return "{:02d}".format(int(re.sub('[^0-9]','', match.group())))
        else:
            return False

    def call_tvdb(self):
        tvdb.KEYS.API_KEY = environ["TVDBKEY"]
        results = []
        title = self.title.replace(self.year, "").strip() if self.year else self.title.strip()
        search = tvdb.Search()
        response = search.series(title)
        for r in response:
            if self.year:
                if self.year in r["firstAired"]:
                    results.append(r["seriesName"])
            else:
                results.append(r["seriesName"])
        return results

    def cross_check_titles(self):
        """
        This makes calls to the TVDB, OMDB, and TMDB APIs and stores the results
        of those calls the 'tvdb', 'omdb', and 'tmdb' variables.  If the result is not
        an empty list it is added to the 'results' list and passed to 'match_title'.
        """
        tvdb = self.call_tvdb()
        omdb = self.call_omdb()
        tmdb = self.call_tmdb()
        results = []
        for call_result in [tvdb, omdb, tmdb]:
            if len(call_result) > 0:
                results += call_result
        if len(results) > 0:
            return self.match_title(results)
        else:
            return self.title
