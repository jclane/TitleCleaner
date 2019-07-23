# TitleCleaner

TitleCleaner is a simple Python script that I use to rename video files.

## Usage

TitleCleaner can clean one file name at a time.
```
$ python title_cleaner.py PATH-TO-FILE/FILE-TO-CLEAN.mkv PATH-TO-COPY-TO/
```
Or, using the `-D` flag, TitleCleaner can walk through a folder and clean any video file names it finds.
```
$ python title_cleaner.py -D PATH-TO-ORIGINALS/ PATH-TO-COPY-TO/
```

## Updates

### July 17, 20019

Title matching seems to be working well now.  I wonder if I should use this and pull other info from the match.  I could use it to get the year for files without a year.  Perhaps the episode name for TV shows.

#### July 7, 2019

Add `argparse` so script can be ran with arguments.  I'm wanting to set this up as a cron job eventually.  Also removed unused imports and moved the various classes to the 'classes.py' file.
