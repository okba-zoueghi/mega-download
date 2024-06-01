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
import re
import os
import time
import shutil
import sys
from datetime import datetime
import shlex
from enum import Enum
from fritzbox.fritzbox import Fritzbox, RequestError
from fileutils import FileUtils
from changeipcallback import ChangeIpException, change_ip_address
from spawnhelper import SpawnStatus, SpawnHelper
from colortext import color_text

DATA_THRESHOLD = 4500.0

class DownloadStatus(Enum):
    """
    Enum to represent different download statuses.
    """
    NO_ERROR = 0
    TIMEOUT_EXCEEDED = 1
    DOWNLOAD_FAILED = 100

class MegaDownloadException(Exception):
    def __init__(self, message):
        super().__init__(message)

class MegaCmdHelper:
    def __init__(self):
        pass

    @staticmethod
    def mega_get(file, target_folder, timeout):
        status = DownloadStatus.NO_ERROR
        command = f"mega-get {file} {target_folder}"
        print(f'Downloading of file/link: {file} ...')
        spawn_status, process_exit_code, output = SpawnHelper.spawn(command, timeout)
        if spawn_status == SpawnStatus.NO_ERROR:
            if process_exit_code != 0:
                status = DownloadStatus.DOWNLOAD_FAILED
                print(color_text(f'mega-get failed with error code: {process_exit_code}', 'RED'))
                print(color_text(f"mega-get output:\n[{output}]", 'RED'))
        elif spawn_status == SpawnStatus.TIMEOUT:
            status = DownloadStatus.TIMEOUT_EXCEEDED
        else:
            status = DownloadStatus.DOWNLOAD_FAILED
        return (output, status)

    @staticmethod
    def is_file_link(link):
        return (("mega.nz/file/" in link) or ("mega.nz/#!" in link))

    @staticmethod
    def logout():
        """
        Log out from public link.
        """
        spawn_status, process_exit_code, output = SpawnHelper.spawn("mega-logout")
        if spawn_status == SpawnStatus.NO_ERROR:
            if process_exit_code != 0:
                raise MegaDownloadException(f"Logout failed with error code: {process_exit_code}\n{output}")
        elif spawn_status == SpawnStatus.TIMEOUT:
            raise MegaDownloadException('Logout failed due to timeout')
        else:
            raise MegaDownloadException('Logout failed due to unexpected error')

    @staticmethod
    def is_logged_in():
        """
        Check if a login to public link is active.

        :return: True if logged in, False otherwise.
        """
        spawn_status, process_exit_code, output = SpawnHelper.spawn("mega-ls")
        is_logged_in = True
        if spawn_status == SpawnStatus.NO_ERROR:
            if process_exit_code != 0:
                is_logged_in = False
        elif spawn_status == SpawnStatus.TIMEOUT:
            raise MegaDownloadException('Login check failed due to timeout')
        else:
            raise MegaDownloadException('Login check failed due to unexpected error')
        return is_logged_in

    @staticmethod
    def login(folder_link):
        """
        Log in to the public link.
        """
        spawn_status, process_exit_code, output = SpawnHelper.spawn(f"mega-login {folder_link}")
        if spawn_status == SpawnStatus.NO_ERROR:
            if process_exit_code != 0:
                raise MegaDownloadException(f"Loging failed with error code: {process_exit_code}\n{output}")
        elif spawn_status == SpawnStatus.TIMEOUT:
            raise MegaDownloadException('Login failed due to timeout')
        else:
            raise MegaDownloadException('Login failed due to unexpected error')

    @staticmethod
    def list_all_files():
        """
        Retrieve the file paths and file names from the public link.

        :return: A list of tuples containing file path, file name and file size.
        """
        # this command list all files exluding folders.
        spawn_status, process_exit_code, output = SpawnHelper.spawn('mega-find -l --size=+0B *')
        if spawn_status == SpawnStatus.NO_ERROR:
            if process_exit_code != 0:
                raise MegaDownloadException(f"mega-find failed with error code: {process_exit_code}\n{output}")
        elif spawn_status == SpawnStatus.TIMEOUT:
            raise MegaDownloadException('mega-find failed due to timeout')
        else:
            raise MegaDownloadException('mega-find failed due to unexpected error')
        mega_find_output = output.strip()
        mega_file_paths_and_file_names = []
        entries = mega_find_output.split('\n')
        size_pattern = re.compile(r"\((\d+\.\d+) (B|KB|MB|GB)\)")
        for entry in entries:
            entry = entry.replace('\r','')
            match = size_pattern.search(entry)
            file_size = float(0)
            if match:
                file_size = float(match.group(1))
                unit = match.group(2)
                if unit == "GB":
                    file_size *= 1024
                elif unit == "KB":
                    file_size /= 1024
                elif unit == "B":
                    file_size /= (1024*1024)
            entry = entry[:match.start()].strip()
            split_entry = entry.split('/')
            download_link = os.path.join(*split_entry)
            posix_path = shlex.quote(download_link)
            file_name = split_entry[-1]
            mega_file_paths_and_file_names.append((posix_path, file_name, file_size))
        return mega_file_paths_and_file_names

class MegaDownloadFile:
    """
    Class to handle downloading a file from Mega.nz public link without quoata restrictions.
    This is achieved through changing the IP address before starting the file download.
    """
    def __init__(self, file_link, target_folder, max_download_time, change_ip_callback = change_ip_address):
        """
        Initialize the MegaDownloadFolder instance.

        :param file_link: The public Mega.nz file link to download from.
        :param target_folder: The folder to download the files to.
        :param max_download_time: Maximum time allowed for the download of a single file in seconds.
        :change_ip_callback: Callback function for changing ip address.
        """
        print(f"####################################### MegaDownloadFile job ended at {datetime.now()} #######################################")
        self.tmp_folder = FileUtils.create_tmp_folder()
        if not FileUtils.does_folder_exist(target_folder):
            raise MegaDownloadException(f'Target folder: {target_folder} does not exist')
        self.file_link = file_link
        self.target_folder = target_folder
        self.max_download_time = max_download_time
        self.change_ip_callback = change_ip_callback
        MegaCmdHelper.logout()

    def __del__(self):
        FileUtils.delete_folder(self.tmp_folder)
        print(f"####################################### MegaDownloadFile job ended at {datetime.now()} #######################################")

    def download_file(self):
        """
        Download file.
        The IP address is changed before the download to avoid exceeding the mega download quota.

        :return: Download status. An exception is thrown is case of fatal error.
        """
        self.change_ip_callback()
        output, status = MegaCmdHelper.mega_get(self.file_link, self.tmp_folder, self.max_download_time)
        if status == DownloadStatus.NO_ERROR:
            FileUtils.move_files_to_destination(self.tmp_folder, self.target_folder)
            print(color_text(f'{self.file_link} is downloaded successfully', 'GREEN'))
        elif status == DownloadStatus.TIMEOUT_EXCEEDED:
            FileUtils.remove_mega_tmp_files(self.tmp_folder)
            print(color_text(f"{datetime.now()} Timeout exceeded during downloading {self.file_link}", 'RED'))
        else:
            FileUtils.remove_mega_tmp_files(self.tmp_folder)
            print(color_text(f"{datetime.now()} Unexpected mega-get error encountered during downloading {self.file_link}", 'RED'))
        return status

class MegaDownloadFolder:
    """
    Class to handle downloading files from Mega.nz folder using public links without quoata restrictions.
    """
    def __init__(self, folder_link, target_folder, max_download_time, change_ip_callback = change_ip_address):
        """
        Initialize the MegaDownloadFolder instance.

        :param folder_link: The public Mega.nz folder link to download from.
        :param target_folder: The folder to download the files to.
        :param max_download_time: Maximum time allowed for the download of a single file in seconds.
        :change_ip_callback: Callback function for changing ip address.
        """
        print(f"####################################### MegaDownloadFolder job started at {datetime.now()} #######################################")
        self.tmp_folder = FileUtils.create_tmp_folder()
        if not FileUtils.does_folder_exist(target_folder):
            raise MegaDownloadException(f'Target folder: {target_folder} does not exist')
        self.folder_link = folder_link
        self.target_folder = target_folder
        self.max_download_time = max_download_time
        self.change_ip_callback = change_ip_callback
        MegaCmdHelper.logout()
        MegaCmdHelper.login(self.folder_link)

    def __del__(self):
        FileUtils.delete_folder(self.tmp_folder)
        print(f"####################################### MegaDownloadFolder job ended at {datetime.now()} #######################################")

    def _get_mega_download_paths_of_missing_files(self, mega_file_paths_and_file_names):
        mega_download_paths = []
        for mega_file_path, file_name, file_size in mega_file_paths_and_file_names:
            if not FileUtils.folder_contains_file(self.target_folder, file_name):
                print(color_text(f'File missing: {file_name} (Size: {file_size} MB)', 'YELLOW'))
                mega_download_paths.append((mega_file_path, file_size))
            else:
                print(color_text(f'File already exists: {file_name} (Size: {file_size} MB)', 'GREEN'))
        if not mega_download_paths:
            print(color_text('No file is missing', GREEN))
        return mega_download_paths

    def download_files(self):
        """
        Download missing files.
        The IP address is changed initially and then each time the downloaded data reaches DATA_THRESHOLD

        :return: list of files and their download status. An exception is thrown is case of fatal error.
        """
        download_status = []
        downloaded_data_since_ip_change = DATA_THRESHOLD
        total_downloaded_data = 0.0
        mega_file_paths_and_file_names = MegaCmdHelper.list_all_files()
        mega_download_paths = self._get_mega_download_paths_of_missing_files(mega_file_paths_and_file_names)
        if mega_download_paths:
            for mega_file_path, file_size in mega_download_paths:
                if (downloaded_data_since_ip_change + file_size) >= DATA_THRESHOLD:
                    MegaCmdHelper.logout()
                    self.change_ip_callback()
                    MegaCmdHelper.login(self.folder_link)
                    downloaded_data_since_ip_change = 0
                print(color_text(f'Downloaded data since last IP address change: {downloaded_data_since_ip_change} MB', 'YELLOW'))
                output, status = MegaCmdHelper.mega_get(mega_file_path, self.tmp_folder, self.max_download_time)
                download_status.append((mega_file_path, status))
                if status == DownloadStatus.NO_ERROR:
                    total_downloaded_data += file_size
                    FileUtils.move_files_to_destination(self.tmp_folder, self.target_folder)
                    print(color_text(f'{mega_file_path} is downloaded successfully', 'GREEN'))
                    print(color_text(f'Total downloaded data: {total_downloaded_data} MB', 'GREEN'))
                elif status == DownloadStatus.TIMEOUT_EXCEEDED:
                    FileUtils.remove_mega_tmp_files(self.tmp_folder)
                    print(color_text(f"{datetime.now()} Timeout exceeded during downloading {mega_file_path}", 'RED'))
                else:
                    FileUtils.remove_mega_tmp_files(self.tmp_folder)
                    print(color_text(f"{datetime.now()} Unexpected mega-get error encountered during downloading {mega_file_path}", 'RED'))
                downloaded_data_since_ip_change += file_size
        return download_status
