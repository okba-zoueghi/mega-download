#!/usr/bin/env python3

# Copyright (C) 2024
#
# Author: okba.zoueghi@gmail.com
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

import argparse
from megadownload import MegaDownload

max_download_time = 3600

# Parse args
parser = argparse.ArgumentParser(description='Looks for missing files in target folder and downloads them with changing the IP address before each file download')
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
