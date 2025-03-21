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

import os
import re
import shlex
import shutil
import sys
import threading
import time
from datetime import datetime
from enum import Enum

import pexpect

from colortext import color_text, print_progress_bar
from fileutils import FileUtils
from fritzbox.fritzbox import Fritzbox, RequestError
from ipaddresschanger import ChangeIpException, IpChangerHelper
from spawnhelper import SpawnHelper, SpawnStatus

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
        print(f"Downloading of file/link: {file} ...")
        spawn_status, process_exit_code, output = SpawnHelper.spawn(command, timeout)
        if spawn_status == SpawnStatus.NO_ERROR:
            if process_exit_code != 0:
                status = DownloadStatus.DOWNLOAD_FAILED
                print(
                    color_text(
                        f"mega-get failed with error code: {process_exit_code}", "RED"
                    )
                )
                print(color_text(f"mega-get output:\n[{output}]", "RED"))
        elif spawn_status == SpawnStatus.TIMEOUT:
            status = DownloadStatus.TIMEOUT_EXCEEDED
        else:
            status = DownloadStatus.DOWNLOAD_FAILED
        return (output, status)

    @staticmethod
    def is_file_link(link):
        return ("mega.nz/file/" in link) or ("mega.nz/#!" in link)

    @staticmethod
    def logout():
        """
        Log out from public link.
        """
        spawn_status, process_exit_code, output = SpawnHelper.spawn("mega-logout")
        if spawn_status == SpawnStatus.NO_ERROR:
            if process_exit_code != 0:
                raise MegaDownloadException(
                    f"Logout failed with error code: {process_exit_code}\n{output}"
                )
        elif spawn_status == SpawnStatus.TIMEOUT:
            raise MegaDownloadException("Logout failed due to timeout")
        else:
            raise MegaDownloadException("Logout failed due to unexpected error")

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
            raise MegaDownloadException("Login check failed due to timeout")
        else:
            raise MegaDownloadException("Login check failed due to unexpected error")
        return is_logged_in

    @staticmethod
    def login(folder_link):
        """
        Log in to the public link.
        """
        spawn_status, process_exit_code, output = SpawnHelper.spawn(
            f"mega-login {folder_link}"
        )
        if spawn_status == SpawnStatus.NO_ERROR:
            if process_exit_code != 0:
                raise MegaDownloadException(
                    f"Loging failed with error code: {process_exit_code}\n{output}"
                )
        elif spawn_status == SpawnStatus.TIMEOUT:
            raise MegaDownloadException("Login failed due to timeout")
        else:
            raise MegaDownloadException("Login failed due to unexpected error")

    @staticmethod
    def kill_mega_cmd_server():
        kill_server_command = "pkill mega-cmd-server"
        spawn_status, process_exit_code, output = SpawnHelper.spawn(kill_server_command)
        if spawn_status == SpawnStatus.NO_ERROR:
            if process_exit_code != 0:
                MegaDownloadException(
                    f"Killing mega-cmd-server failed with error code: {process_exit_code}\n{output}"
                )
        elif spawn_status == SpawnStatus.TIMEOUT:
            raise MegaDownloadException("Killing mega-cmd-server failed due to timeout")
        else:
            raise MegaDownloadException(
                "Killing mega-cmd-server failed due to unexpected error"
            )

    @staticmethod
    def start_mega_cmd_server():
        start_server_command = "mega-transfers"
        spawn_status, process_exit_code, output = SpawnHelper.spawn(
            start_server_command
        )
        if spawn_status == SpawnStatus.NO_ERROR:
            if process_exit_code != 0:
                MegaDownloadException(
                    f"Starting mega-cmd-server failed with error code: {process_exit_code}\n{output}"
                )
        elif spawn_status == SpawnStatus.TIMEOUT:
            raise MegaDownloadException(
                "Starting mega-cmd-server failed due to timeout"
            )
        else:
            raise MegaDownloadException(
                "Starting mega-cmd-server failed due to unexpected error"
            )

    @staticmethod
    def get_file_info_from_link(file_link):
        mega_get_command = f"mega-get -q {file_link} /tmp"
        mega_transfers_command = f"mega-transfers --col-separator='|||' --output-cols=DESTINYPATH,STATE,PROGRESS"
        spawn_status, process_exit_code, output = SpawnHelper.spawn(mega_get_command)
        if spawn_status == SpawnStatus.NO_ERROR:
            if process_exit_code != 0:
                raise MegaDownloadException(
                    f"Get file name failed, command '{mega_get_command}' failed with exit code {process_exit_code}\noutput: {output}"
                )
        else:
            raise MegaDownloadException(f"Get file name failed")
        spawn_status, process_exit_code, output = SpawnHelper.spawn(
            mega_transfers_command
        )
        if spawn_status == SpawnStatus.NO_ERROR:
            if process_exit_code != 0:
                raise MegaDownloadException(
                    f"Get file name failed, command '{mega_transfers_command}' failed with exit code {process_exit_code}\noutput: {output}"
                )
        else:
            raise MegaDownloadException(f"Get file name failed")
        download_info = MegaCmdHelper.parse_mega_transfers_output(output)
        if not download_info:
            raise MegaDownloadException(f"Get file name failed")
        file_destination, state, progress = download_info[0]
        file_name = file_destination.split("/")[-1]
        file_size = float(0)
        size_pattern = re.compile(r"(\d+\.\d+) (B|KB|MB|GB)")
        match = size_pattern.search(progress)
        if match:
            file_size = float(match.group(1))
            unit = match.group(2)
            if unit == "GB":
                file_size *= 1024
            elif unit == "KB":
                file_size /= 1024
            elif unit == "B":
                file_size /= 1024 * 1024
        else:
            raise MegaDownloadException(f"Get file size failed")
        mega_transfers_command = f"mega-transfers -c -a"
        spawn_status, process_exit_code, output = SpawnHelper.spawn(
            mega_transfers_command
        )
        if spawn_status == SpawnStatus.NO_ERROR:
            if process_exit_code != 0:
                raise MegaDownloadException(
                    f"Get file name failed, command '{mega_transfers_command}' failed with exit code {process_exit_code}\noutput: {output}"
                )
        else:
            raise MegaDownloadException(f"Get file name failed")
        return file_name, file_size

    @staticmethod
    def print_progress(period, download_start_time, file_size):
        time.sleep(10)
        while True:
            check_mega_cmd_command = f"pgrep -l mega-cmd-server"
            spawn_status, process_exit_code, output = SpawnHelper.spawn(check_mega_cmd_command)
            if spawn_status == SpawnStatus.NO_ERROR:
                if process_exit_code != 0:
                    continue
            mega_transfers_command = f"mega-transfers --col-separator='|||' --output-cols=DESTINYPATH,STATE,PROGRESS"
            spawn_status, process_exit_code, output = SpawnHelper.spawn(mega_transfers_command)
            if spawn_status == SpawnStatus.NO_ERROR:
                if process_exit_code != 0:
                    raise MegaDownloadException(f"Print progress failed, command '{mega_transfers_command}' failed with exit code {process_exit_code}\noutput: {output}")
            else:
                raise MegaDownloadException(f"Print progress failed")
            download_info = MegaCmdHelper.parse_mega_transfers_output(output)
            if not download_info:
                print()
                break
            pattern = r"(\d+\.\d+|\d+)%"
            match = re.search(pattern, download_info[0][2])
            if match:
                progress = float(match.group(1))
                downloaded_data = round(((progress * file_size) / 100), 1)
                current_time = time.time()
                download_time_in_seconds = current_time - download_start_time
                average_download_speed = int((file_size / download_time_in_seconds) * 8)
                print_progress_bar(progress, downloaded_data, average_download_speed)
            else:
                raise MegaDownloadException(f"Print progress failed")
            time.sleep(period)

    @staticmethod
    def parse_mega_transfers_output(output):
        download_infos = []
        valid_states = (
            "QUEUED|ACTIVE|PAUSED|RETRYING|COMPLETING|COMPLETED|CANCELLED|FAILED"
        )
        entries = output.strip().replace("\r", "").split("\n")
        start_index = 0
        if len(entries) > 1:
            for i in range(0, len(entries)):
                if "|||" in entries[i]:
                    start_index = i
                    break
            col_name = entries[start_index].split("|||")
            if (
                (len(col_name) == 3)
                and (col_name[0] == "DESTINYPATH")
                and (col_name[1] == "STATE")
                and (col_name[2] == "PROGRESS")
            ):
                for entry in entries[(start_index + 1) :]:
                    download_info = entry.split("|||")
                    if (len(download_info) == 3) and (download_info[1] in valid_states):
                        download_infos.append(
                            (download_info[0], download_info[1], download_info[2])
                        )
        return download_infos

    @staticmethod
    def download_file_from_folder(mega_file_path, filename, target_folder, ip_changer):
        download_status = DownloadStatus.DOWNLOAD_FAILED
        mega_get_command = f"mega-get -q {mega_file_path} {target_folder}"
        spawn_status, process_exit_code, output = SpawnHelper.spawn(mega_get_command)
        if spawn_status == SpawnStatus.NO_ERROR:
            if process_exit_code != 0:
                print(color_text(f"{datetime.now()} Command '{mega_get_command}' failed with exit code {process_exit_code}\noutput: {output}","RED"))

        if (spawn_status == SpawnStatus.NO_ERROR) and (process_exit_code == 0):
            print(f"Downloading of large file: {filename} ...")
            time.sleep(5)
            while True:
                mega_transfers_command = f"mega-transfers --col-separator='|||' --output-cols=DESTINYPATH,STATE,PROGRESS"
                spawn_status, process_exit_code, output = SpawnHelper.spawn(mega_transfers_command)
                if spawn_status == SpawnStatus.NO_ERROR:
                    if process_exit_code != 0:
                        print(color_text(f"{datetime.now()} Command '{mega_transfers_command}' failed with exit code {process_exit_code}\noutput: {output}","RED"))
                        break
                    else:
                        download_infos = MegaCmdHelper.parse_mega_transfers_output(output)
                        if download_infos:
                            for file_destination, state, progress in download_infos:
                                if filename in file_destination:
                                    if state == "RETRYING":
                                        MegaCmdHelper.kill_mega_cmd_server()
                                        print(color_text(f"{datetime.now()} Quota exceeded, killed mega-cmd-server and changing IP address","RED"))
                                        ip_changer.change_ip()
                                        print(color_text(f"{datetime.now()} Starting the mega-cmd-server...", "RED")
                                        )
                                        MegaCmdHelper.start_mega_cmd_server()
                                        time.sleep(5)
                                    break

                        # empty output --> no download is active --> download might be completed
                        elif output.replace("\r", "").replace("\n", "") == "":
                            time.sleep(5)
                            print(color_text(f"Checking download status", "YELLOW"))
                            mega_transfers_command = f"mega-transfers --col-separator='|||' --output-cols=DESTINYPATH,STATE,PROGRESS --show-completed"
                            spawn_status, process_exit_code, output = SpawnHelper.spawn(mega_transfers_command)
                            if spawn_status == SpawnStatus.NO_ERROR:
                                if process_exit_code != 0:
                                    print(color_text(f"{datetime.now()} Command '{mega_transfers_command}' failed with exit code {process_exit_code}\noutput: {output}", "RED"))
                                    break
                                else:
                                    completing_download = False
                                    download_infos = MegaCmdHelper.parse_mega_transfers_output(output)
                                    for (file_destination, state, progress) in download_infos:
                                        if filename in file_destination:
                                            if state == "COMPLETED":
                                                download_status = DownloadStatus.NO_ERROR
                                                break
                                            elif state == "COMPLETING":
                                                print(color_text(f"{datetime.now()} Download is being completed", "YELLOW"))
                                                completing_download = True
                                                break
                                            else:
                                                print(color_text(f"{datetime.now()} Unxpect download state encountered '{state}'", "YELLOW"))
                                    if not completing_download:
                                        break
                        else:
                            print(color_text(f"{datetime.now()} Unexpected mega-transfers output: [{output}]", "RED"))
                            break
                        time.sleep(1)
                elif spawn_status == SpawnStatus.TIMEOUT:
                    print(color_text(f"{datetime.now()} Timeout exceeded during running command '{mega_transfers_command}'", "RED"))
                    break
                else:
                    print(color_text(f"{datetime.now()} Unexpected error running command '{mega_transfers_command}'", "RED"))
                    break

        return download_status

    @staticmethod
    def list_all_files():
        """
        Retrieve the file paths and file names from the public link.

        :return: A list of tuples containing file path, file name and file size.
        """
        # this command list all files exluding folders.
        spawn_status, process_exit_code, output = SpawnHelper.spawn(
            "mega-find -l --size=+0B *"
        )
        if spawn_status == SpawnStatus.NO_ERROR:
            if process_exit_code != 0:
                raise MegaDownloadException(
                    f"mega-find failed with error code: {process_exit_code}\n{output}"
                )
        elif spawn_status == SpawnStatus.TIMEOUT:
            raise MegaDownloadException("mega-find failed due to timeout")
        else:
            raise MegaDownloadException("mega-find failed due to unexpected error")
        mega_find_output = output.strip()
        mega_file_paths_and_file_names = []
        entries = mega_find_output.split("\n")
        size_pattern = re.compile(r"\((\d+\.\d+) (B|KB|MB|GB)\)")
        for entry in entries:
            entry = entry.replace("\r", "")
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
                    file_size /= 1024 * 1024
            entry = entry[: match.start()].strip()
            split_entry = entry.split("/")
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

    def __init__(self, file_link, target_folder, max_download_time):
        """
        Initialize the MegaDownloadFolder instance.

        :param file_link: The public Mega.nz file link to download from.
        :param target_folder: The folder to download the files to.
        :param max_download_time: Maximum time allowed for the download of a single file in seconds.
        """
        print(
            f"####################################### MegaDownloadFile job started at {datetime.now()} #######################################"
        )
        self.tmp_folder = FileUtils.create_tmp_folder()
        if not FileUtils.does_folder_exist(target_folder):
            raise MegaDownloadException(
                f"Target folder: {target_folder} does not exist"
            )
        self.file_link = file_link
        self.target_folder = target_folder
        self.max_download_time = max_download_time
        MegaCmdHelper.logout()

    def __del__(self):
        FileUtils.delete_folder(self.tmp_folder)
        print(
            f"####################################### MegaDownloadFile job ended at {datetime.now()} #######################################"
        )

    def download_file(self):
        """
        Download file.
        The IP address is changed before the download to avoid exceeding the mega download quota.

        :return: Download status. An exception is thrown is case of fatal error.
        """
        status = DownloadStatus.DOWNLOAD_FAILED
        file_name, file_size = MegaCmdHelper.get_file_info_from_link(self.file_link)
        print(
            color_text(
                f"File link contains file: {file_name} ({file_size} MB)", "YELLOW"
            )
        )
        ip_changer = IpChangerHelper.get_ip_changer()
        ip_changer.change_ip()
        thread = threading.Thread(
            target=MegaCmdHelper.print_progress,
            args=(
                1,
                time.time(),
                file_size,
            ),
        )
        thread.start()
        start_time = time.time()
        output, status = MegaCmdHelper.mega_get(
            self.file_link, self.tmp_folder, self.max_download_time
        )
        end_time = time.time()
        download_time_in_seconds = end_time - start_time
        download_speed = int((file_size / download_time_in_seconds) * 8)
        thread.join()
        if status == DownloadStatus.NO_ERROR:
            print(
                color_text(
                    f"{file_name} is downloaded successfully in {round(download_time_in_seconds / 60, 1)} mins (average download speed: {download_speed} Mbps)",
                    "GREEN",
                )
            )
            print(
                color_text(
                    f"Moving file ({file_name}) to destination ({self.target_folder}) ...",
                    "YELLOW",
                )
            )
            FileUtils.move_files_to_destination(self.tmp_folder, self.target_folder)
            print(color_text(f"{file_name} is moved to destination", "GREEN"))
        elif status == DownloadStatus.TIMEOUT_EXCEEDED:
            FileUtils.remove_mega_tmp_files(self.tmp_folder)
            print(
                color_text(
                    f"{datetime.now()} Timeout exceeded during downloading {self.file_link}",
                    "RED",
                )
            )
        else:
            FileUtils.remove_mega_tmp_files(self.tmp_folder)
            print(
                color_text(
                    f"{datetime.now()} Unexpected mega-get error encountered during downloading {self.file_link}",
                    "RED",
                )
            )
        return status


class MegaDownloadFolder:
    """
    Class to handle downloading files from Mega.nz folder using public links without quoata restrictions.
    """

    def __init__(self, folder_link, target_folder, max_download_time):
        """
        Initialize the MegaDownloadFolder instance.

        :param folder_link: The public Mega.nz folder link to download from.
        :param target_folder: The folder to download the files to.
        :param max_download_time: Maximum time allowed for the download of a single file in seconds.
        """
        print(
            f"####################################### MegaDownloadFolder job started at {datetime.now()} #######################################"
        )
        self.tmp_folder = FileUtils.create_tmp_folder()
        if not FileUtils.does_folder_exist(target_folder):
            raise MegaDownloadException(
                f"Target folder: {target_folder} does not exist"
            )
        self.folder_link = folder_link
        self.target_folder = target_folder
        self.max_download_time = max_download_time
        MegaCmdHelper.logout()
        MegaCmdHelper.login(self.folder_link)

    def __del__(self):
        MegaCmdHelper.logout()
        FileUtils.delete_folder(self.tmp_folder)
        print(
            f"####################################### MegaDownloadFolder job ended at {datetime.now()} #######################################"
        )

    def _get_mega_download_paths_of_missing_files(self, mega_file_paths_and_file_names):
        mega_download_paths = []
        for mega_file_path, file_name, file_size in mega_file_paths_and_file_names:
            if not FileUtils.folder_contains_file(self.target_folder, file_name):
                print(
                    color_text(
                        f"File missing: {file_name} (Size: {file_size} MB)", "YELLOW"
                    )
                )
                mega_download_paths.append((mega_file_path, file_name, file_size))
            else:
                print(
                    color_text(
                        f"File already exists: {file_name} (Size: {file_size} MB)",
                        "GREEN",
                    )
                )
        if not mega_download_paths:
            print(color_text("No file is missing", "GREEN"))
        return mega_download_paths

    def download_files(self):
        """
        Download missing files.

        :return: list of files and their download status. An exception is thrown is case of fatal error.
        """
        download_status = []
        total_downloaded_data = 0.0
        mega_file_paths_and_file_names = MegaCmdHelper.list_all_files()
        mega_download_paths = self._get_mega_download_paths_of_missing_files(mega_file_paths_and_file_names)
        ip_changer = IpChangerHelper.get_ip_changer()
        if mega_download_paths:
            for mega_file_path, filename, file_size in mega_download_paths:
                thread = threading.Thread(target=MegaCmdHelper.print_progress, args=(1, time.time(), file_size,),)
                thread.start()
                start_time = time.time()
                status = MegaCmdHelper.download_file_from_folder(mega_file_path, filename, self.tmp_folder, ip_changer)
                thread.join()
                end_time = time.time()
                download_time_in_seconds = end_time - start_time
                download_speed = int((file_size / download_time_in_seconds) * 8)
                download_status.append((mega_file_path, status))
                if status == DownloadStatus.NO_ERROR:
                    total_downloaded_data += file_size
                    print(color_text(f"{filename} is downloaded successfully in {round(download_time_in_seconds / 60, 1)} mins (average download speed: {download_speed} Mbps)", "GREEN"))
                    print(color_text(f"Moving file ({filename}) to destination ({self.target_folder}) ...", "WHITE"))
                    FileUtils.move_files_to_destination(self.tmp_folder, self.target_folder)
                    print(color_text(f"{filename} is moved to destination", "GREEN"))
                    print(color_text(f"Total downloaded data: {total_downloaded_data} MB", "CYAN"))
                else:
                    FileUtils.remove_mega_tmp_files(self.tmp_folder)
                    print(color_text(f"{datetime.now()} Unexpected error encountered during downloading large file{mega_file_path}", "RED"))    
        return download_status
