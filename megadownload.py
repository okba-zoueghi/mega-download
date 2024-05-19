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

import pexpect
import os
import time
import shutil
import sys
from datetime import datetime
import shlex
from enum import Enum
from fritzbox.fritzbox import Fritzbox, RequestError
from fileutils import FileUtils

class DownloadStatus(Enum):
    NO_ERROR = 0
    QUOTA_EXCEEDED = 1
    TIMEOUT_EXCEEDED = 2
    FAILED_TO_CHANGE_IP = 3
    OTHER_MEGA_GET_ERROR = 100

class MegaDownload:
    def __init__(self, public_link, target_folder, max_download_time):
        print(f"####################################### Megadownload job started at {datetime.now()} #######################################")
        self.public_link = public_link
        self.target_folder = target_folder
        self.max_download_time = max_download_time
        self.fritzbox = Fritzbox('http://fritz.box:49000')
        self.tmp_folder = FileUtils.create_tmp_folder()
        self._login()

    def __del__(self):
        self._logout()
        FileUtils.delete_folder(self.tmp_folder)
        print(f"####################################### Megadownload job ended at {datetime.now()} #######################################")

    def _login(self):
        p = pexpect.spawn(f"mega-login {self.public_link}")
        p.expect(pexpect.EOF)

    def _logout(self):
        p = pexpect.spawn('mega-logout')
        p.expect(pexpect.EOF)

    @staticmethod
    def is_logged_in():
        p = pexpect.spawn('mega-ls')
        return (p.wait() == 0)


    def _mega_get(self, mega_file_path):
        command = f"mega-get {mega_file_path} {self.tmp_folder}"
        print(f'Download of file -- {mega_file_path} -- is ongoing...')
        get = pexpect.spawn(command, timeout=self.max_download_time)
        output = ''
        status = DownloadStatus.NO_ERROR

        try:
            output = get.read().decode()
        except KeyboardInterrupt:
            sys.exit(1)
        except Exception as e:
            status = DownloadStatus.TIMEOUT_EXCEEDED
            print(f"Timeout exceeded for downloading file at {datetime.now()}")

        get.close()

        if (status == DownloadStatus.NO_ERROR) and (get.exitstatus != 0):
            if get.exitstatus == 11:
                status = DownloadStatus.QUOTA_EXCEEDED
            else:
                status = DownloadStatus.OTHER_MEGA_GET_ERROR

        print('mega-get finished with status: ', status, ' ', get.exitstatus)
        return (output, status)

    @staticmethod
    def _has_extension(filename):
        parts = filename.rsplit('.', 1)
        return len(parts) == 2 and len(parts[1]) > 0

    def _get_mega_file_path_and_file_name(self):
        p = pexpect.spawn('mega-find *')
        p.expect(pexpect.EOF)
        mega_find_output = p.before.decode().strip()
        mega_file_paths_and_file_names = []
        entries = mega_find_output.split('\n')
        for entry in entries:
            entry = entry.replace('\r','')
            if self._has_extension(entry):
                split_entry = entry.split('/')
                download_link = os.path.join(*split_entry)
                posix_path = shlex.quote(download_link)
                file_name = split_entry[-1]
                mega_file_paths_and_file_names.append((posix_path, file_name))
        return mega_file_paths_and_file_names

    def _get_mega_download_paths_of_missing_files(self, mega_file_paths_and_file_names):
        mega_download_paths = []
        for mega_file_path, file_name in mega_file_paths_and_file_names:
            if not FileUtils.folder_contains_file(self.target_folder, file_name):
                print('File missing: ', file_name)
                mega_download_paths.append(mega_file_path)
        if not mega_download_paths:
            print('No file is missing')
        return mega_download_paths

    def download_files(self):
        status = DownloadStatus.NO_ERROR
        mega_file_paths_and_file_names = self._get_mega_file_path_and_file_name()
        while True:
            mega_download_paths = self._get_mega_download_paths_of_missing_files(mega_file_paths_and_file_names)
            if not mega_download_paths:
                break

            unexpected_error = False
            ip_change_failure = False
            for mega_file_path in mega_download_paths:
                self._logout()
                print('Changing IP address')
                print('Current IP: ', self.fritzbox.get_public_ip())
                change_ip_error_code = self.fritzbox.change_ip_address_block()
                if change_ip_error_code != RequestError.NO_ERROR:
                    ip_change_failure = True
                    status = DownloadStatus.FAILED_TO_CHANGE_IP
                    break
                print('New IP: ', self.fritzbox.get_public_ip())
                self._login()
                output, status = self._mega_get(mega_file_path)
                if status == DownloadStatus.TIMEOUT_EXCEEDED:
                    FileUtils.remove_mega_tmp_files(self.tmp_folder)
                elif status == DownloadStatus.NO_ERROR:
                    FileUtils.move_files_to_destination(self.tmp_folder, self.target_folder)
                else:
                    unexpected_error = True
                    break

            if unexpected_error:
                print(f"{datetime.now()} Unexpected mega-get error encountered, aborting...")
                break

            if ip_change_failure:
                print(f"{datetime.now()} Failed to change the IP address, aborting...")
                break

        return status
