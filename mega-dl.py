#!/usr/bin/env python

import argparse
from megadownload import MegaDownload

max_download_time = 3600

# Parse args
parser = argparse.ArgumentParser(prog='mega-download', description='Looks for missing files in target folder and downloads them')
parser.add_argument('-l', '--link', action='append')
parser.add_argument('-t', '--target-folder')
args = parser.parse_args()
mega_folder_links = args.link
target_folder = args.target_folder


if MegaDownload.is_logged_in():
    print("Session ongoing, aborting...")
else:
    for mega_folder_link in mega_folder_links:
        mega_download = MegaDownload(mega_folder_link, target_folder, max_download_time)
        mega_download.download_files()
