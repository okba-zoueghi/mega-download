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
from changeipcallback import ChangeIpException, change_ip_address

class DownloadStatus(Enum):
    """
    Enum to represent different download statuses.
    """
    NO_ERROR = 0
    QUOTA_EXCEEDED = 1
    TIMEOUT_EXCEEDED = 2
    FAILED_TO_CHANGE_IP = 3
    OTHER_MEGA_GET_ERROR = 100

class MegaDownloadException(Exception):
    def __init__(self, message):
        super().__init__(message)

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
        self.file_link = file_link
        self.target_folder = target_folder
        self.max_download_time = max_download_time
        self.tmp_folder = FileUtils.create_tmp_folder()
        self.change_ip_callback = change_ip_callback

    def __del__(self):
        """
        Destructor to handle cleanup operations.
        """
        FileUtils.delete_folder(self.tmp_folder)
        print(f"####################################### MegaDownloadFile job ended at {datetime.now()} #######################################")

    @staticmethod
    def is_file_link(link):
        return (("mega.nz/file/" in link) or ("mega.nz/#!" in link))

    @staticmethod
    def _spawn(command, timeout=30):
        output = ''
        failure = ''
        timed_out = False
        p = pexpect.spawn(command, timeout=timeout)
        try:
            output = p.read().decode()
        except pexpect.TIMEOUT:
            timed_out = True
            failure = "Process timed out."
            print(failure)
        except pexpect.ExceptionPexpect as e:
            failure = f"An error occurred: {e}"
            print(failure)
        except Exception as e:
            failure = f"An unexpected error occurred: {e}"
            print(failure)
        p.close()
        exit_code = p.exitstatus
        return (exit_code, output, failure, timed_out)

    def _mega_get(self, file_link):
        """
        Download a file from Mega.nz.

        :param mega_file_path: The path of the file to download.
        :return: A tuple containing the output and the download status.
        """
        status = DownloadStatus.NO_ERROR
        command = f"mega-get {file_link} {self.tmp_folder}"
        print(f'Download of file -- {file_link} -- is ongoing...')
        exit_code, output, failure, timed_out = MegaDownloadFile._spawn(command, self.max_download_time)
        if timed_out:
            print(f"Timeout exceeded for downloading file at {datetime.now()}")
            status = DownloadStatus.TIMEOUT_EXCEEDED

        if (status == DownloadStatus.NO_ERROR) and (exit_code != 0):
            if exit_code == 11:
                status = DownloadStatus.QUOTA_EXCEEDED
            else:
                status = DownloadStatus.OTHER_MEGA_GET_ERROR
        print('mega-get finished with status: ', status, ' and exit code: ', exit_code)
        return (output, status)

    def download_file(self):
        """
        Download file.
        The IP address is changed before the download to avoid exceeding the mega download quota.

        :return: If download fails the functions throws MegaDownloadException or ChangeIpException, otherwise the file is
        downloaded successfully.
        """
        self.change_ip_callback()
        output, status = self._mega_get(self.file_link)
        if status == DownloadStatus.NO_ERROR:
            FileUtils.move_files_to_destination(self.tmp_folder, self.target_folder)
        elif status == DownloadStatus.TIMEOUT_EXCEEDED:
            raise MegaDownloadException(f"{datetime.now()} Timeout exceeded during downloading {self.file_link}")
        else:
            raise MegaDownloadException(f"{datetime.now()} Unexpected mega-get error encountered during downloading {self.file_link}")

class MegaDownloadFolder:
    """
    Class to handle downloading files from Mega.nz folder using public links without quoata restrictions.
    This is achieved through changing the IP address before starting each file download.
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
        self.folder_link = folder_link
        self.target_folder = target_folder
        self.max_download_time = max_download_time
        self.tmp_folder = FileUtils.create_tmp_folder()
        self.change_ip_callback = change_ip_callback
        self._login()

    def __del__(self):
        """
        Destructor to handle cleanup operations.
        """
        FileUtils.delete_folder(self.tmp_folder)
        self.logout()
        print(f"####################################### MegaDownloadFolder job ended at {datetime.now()} #######################################")

    @staticmethod
    def _spawn(command, timeout=30):
        output = ''
        failure = ''
        timed_out = False
        p = pexpect.spawn(command, timeout=timeout)
        try:
            output = p.read().decode()
        except pexpect.TIMEOUT:
            timed_out = True
            failure = "Process timed out."
            print(failure)
        except pexpect.ExceptionPexpect as e:
            failure = f"An error occurred: {e}"
            print(failure)
        except Exception as e:
            failure = f"An unexpected error occurred: {e}"
            print(failure)
        p.close()
        exit_code = p.exitstatus
        return (exit_code, output, failure, timed_out)


    def _login(self):
        """
        Log in to the public link.
        """
        exit_code, output, failure, timed_out = MegaDownloadFolder._spawn(f"mega-login {self.folder_link}")
        if exit_code != 0:
            error_msg = f'Login failed with exit code {exit_code}'
            print(error_msg)
            raise MegaDownloadException(error_msg)


    @staticmethod
    def logout():
        """
        Log out from public link.
        """
        exit_code, output, failure, timed_out = MegaDownloadFolder._spawn("mega-logout")
        if exit_code != 0:
            error_msg = f'Logout failed with exit code {exit_code}'
            print(error_msg)
            raise MegaDownloadException(error_msg)

    @staticmethod
    def is_logged_in():
        """
        Check if a login to public link is active.

        :return: True if logged in, False otherwise.
        """
        exit_code, output, failure, timed_out = MegaDownloadFolder._spawn("mega-ls")
        if exit_code == None:
            error_msg = f'Login check failed'
            print(error_msg)
            raise MegaDownloadException(error_msg)
        return (exit_code == 0)


    def _mega_get(self, mega_file_path):
        """
        Download a file from Mega.nz.

        :param mega_file_path: The path of the file to download.
        :return: A tuple containing the output and the download status.
        """
        status = DownloadStatus.NO_ERROR
        command = f"mega-get {mega_file_path} {self.tmp_folder}"
        print(f'Download of file -- {mega_file_path} -- is ongoing...')
        exit_code, output, failure, timed_out = MegaDownloadFolder._spawn(command, self.max_download_time)
        if timed_out:
            print(f"Timeout exceeded for downloading file at {datetime.now()}")
            status = DownloadStatus.TIMEOUT_EXCEEDED

        if (status == DownloadStatus.NO_ERROR) and (exit_code != 0):
            if exit_code == 11:
                status = DownloadStatus.QUOTA_EXCEEDED
            else:
                status = DownloadStatus.OTHER_MEGA_GET_ERROR
        print('mega-get finished with status: ', status, ' and exit code: ', exit_code)
        return (output, status)

    @staticmethod
    def _has_extension(filename):
        """
        Check if the filename has an extension.

        :param filename: The name of the file to check.
        :return: True if the file has an extension, False otherwise.
        """
        parts = filename.rsplit('.', 1)
        return len(parts) == 2 and len(parts[1]) > 0

    def _get_mega_file_path_and_file_name(self):
        """
        Retrieve the file paths and file names from the public link.

        :return: A list of tuples containing file paths and file names.
        """
        exit_code, output, failure, timed_out = MegaDownloadFolder._spawn('mega-find *')
        if exit_code != 0:
            error_msg = f'Listing files failed with exit code {exit_code}'
            print(error_msg)
            raise MegaDownloadException(error_msg)
        mega_find_output = output.strip()
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
        """
        Get the download paths of missing files.

        :param mega_file_paths_and_file_names: List of tuples containing file paths and file names.
        :return: A list of mega file paths for files that are missing in the target folder.
        """
        mega_download_paths = []
        for mega_file_path, file_name in mega_file_paths_and_file_names:
            if not FileUtils.folder_contains_file(self.target_folder, file_name):
                print('File missing: ', file_name)
                mega_download_paths.append(mega_file_path)
        if not mega_download_paths:
            print('No file is missing')
        return mega_download_paths

    def download_files(self):
        """
        Download missing files.
        The IP address is changed before every download to avoid exceeding the mega download quota.

        :return: If download fails the functions throws MegaDownloadException or ChangeIpException, otherwise all files are
        downloaded successfully.
        """
        mega_file_paths_and_file_names = self._get_mega_file_path_and_file_name()
        while True:
            mega_download_paths = self._get_mega_download_paths_of_missing_files(mega_file_paths_and_file_names)
            if not mega_download_paths:
                break
            for mega_file_path in mega_download_paths:
                self.logout()
                self.change_ip_callback()
                self._login()
                output, status = self._mega_get(mega_file_path)
                if status == DownloadStatus.NO_ERROR:
                    FileUtils.move_files_to_destination(self.tmp_folder, self.target_folder)
                elif status == DownloadStatus.TIMEOUT_EXCEEDED:
                    FileUtils.remove_mega_tmp_files(self.tmp_folder)
                else:
                    raise MegaDownloadException(f"{datetime.now()} Unexpected mega-get error encountered during downloading {mega_file_path}")
