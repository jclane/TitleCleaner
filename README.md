# TitleCleaner

TitleCleaner is a simple Python script that I use to rename video files.

## Usage

TitleCleaner can clean one file name at a time.
```
$ python TitleCleaner.py PATH-TO-FILE/FILE-TO-CLEAN.mkv PATH-TO-COPY-TO/
```
Or, using the `-r` flag, TitleCleaner can walk through a folder and clean any video file names it finds.
```
$ python TitleCleaner.py -r PATH-TO-ORIGINALS/ PATH-TO-COPY-TO/
```

## Dependencides

The following are required for this to work:

- fuzzywuzzy
- tvdbsimple
- tmdbsimple

## Updates

### July 17, 20019

Title matching seems to be working well now.  I wonder if I should use this and pull other info from the match.  I could use it to get the year for files without a year.  Perhaps the episode name for TV shows.

#### July 7, 2019

Add `argparse` so script can be ran with arguments.  I'm wanting to set this up as a cron job eventually.  Also removed unused imports and moved the various classes to the 'classes.py' file.
