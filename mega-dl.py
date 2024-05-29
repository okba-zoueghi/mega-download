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
from megadownload import MegaDownloadFolder, MegaDownloadFile, MegaDownloadException

# Parse args
parser = argparse.ArgumentParser(description='Looks for missing files in target folder and downloads them with changing the IP address before each file download')
parser.add_argument('-l', '--link', required=True, action='append', help='mega public link')
parser.add_argument('-t', '--target-folder', required=True, help='Target folder absolute path to store successfully downloaded files')
parser.add_argument('-m', '--max-download-time', type=int, default=3600, help='Max download time for a single file in seconds')
parser.add_argument('-f', '--force-logout', action='store_true', help='Force mega logout')

args = parser.parse_args()
mega_links = args.link
target_folder = args.target_folder
max_download_time = args.max_download_time
force_logout = args.force_logout

if force_logout:
    MegaDownloadFolder.logout()

if MegaDownloadFolder.is_logged_in():
    print("Session ongoing, aborting...")
else:
    for link in mega_links:
        try:
            if MegaDownloadFile.is_file_link(link):
                mega_download = MegaDownloadFile(link, target_folder, max_download_time)
                mega_download.download_file()
            else:
                mega_download = MegaDownloadFolder(link, target_folder, max_download_time)
                mega_download.download_files()
                del mega_download
        except MegaDownloadException as e:
            print(f"Fatal error: {e} - aborting download from {link}")
        except Exception as e:
            print(f"An unexpected error occurred: {e} - aborting download from {link}")
