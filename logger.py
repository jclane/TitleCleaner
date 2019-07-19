#!/usr/bin/env Python3
import glob
import logging
import logging.handlers
from datetime import datetime

now = datetime.now()
LOG_FILE = r"titlecleaner.log"

my_logger = logging.getLogger(__name__)
my_logger.setLevel(logging.INFO)

handler = logging.handlers.RotatingFileHandler(
              LOG_FILE, maxBytes=10485760, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
my_logger.addHandler(handler)


def log_msg(lvl, msg):
    if lvl == "info":
        my_logger.info(msg)
    if lvl == "warn":
        my_logger.warning(msg)
    if lvl == "error":
        my_logger.error(msg)
    if lvl == "critical":
        my_logger.critical(msg)

def print_log(logfile="titlecleaner.log"):
    with(open(logfile, "r")) as log:
        print(log.readlines())