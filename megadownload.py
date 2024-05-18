#!/usr/bin/env python

import pexpect
import string
import os
import random
import tempfile
import time
import shutil
import sys
import datetime
import shlex
import requests
from enum import Enum

class DownloadStatus(Enum):
    NO_ERROR = 0
    QUOTA_EXCEEDED = 1
    TIMEOUT_EXCEEDED = 2
    OTHER_MEGA_GET_ERROR = 3

class Fritzbox:
    def ___init__(self):
        pass

    @staticmethod
    def _check_internet_connection():
        try:
            response = requests.get("http://www.google.com", timeout=5)
            response.raise_for_status()  # Raises an exception for bad status codes (4xx or 5xx)
            return True
        except requests.RequestException:
            return False

    @staticmethod
    def change_ip_address():
        reconnect = pexpect.spawn('fritzbox-reconnect.py', timeout=None)
        reconnect.expect(pexpect.EOF)
        print('Changing IP address...')
        time.sleep(10)
        while not Fritzbox._check_internet_connection():
            time.sleep(5)
            print('Changing IP address...')
        print('IP address changed...')


class FileUtils:
    def __init__(self):
        pass

    @staticmethod
    def create_tmp_folder():
        tmp_folder_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))
        tmp_dir = tempfile.gettempdir()
        tmp_folder_path = os.path.join(tmp_dir, tmp_folder_name)
        os.mkdir(tmp_folder_path)
        print('Tmp folder for download : ', tmp_folder_path)
        return tmp_folder_path

    @staticmethod
    def remove_mega_tmp_files(folder_path):
        for filename in os.listdir(folder_path):
            if filename.startswith('.'):
                file_path = os.path.join(folder_path, filename)
                os.remove(file_path)
                print(f"Removed mega tmp file: {file_path}")

    @staticmethod
    def folder_contains_file(folder_path, file_name):
        for root, dirs, files in os.walk(folder_path):
            if file_name in files:
                return True
        return False

    @staticmethod
    def move_files_to_destination(source_folder, destination_folder):
        for root, dirs, files in os.walk(source_folder):
            for file_name in files:
                source_file_path = os.path.join(root, file_name)
                destination_file_path = os.path.join(destination_folder, file_name)
                current_time = datetime.datetime.now()
                print(f"{current_time}: Moving '{file_name}'")
                shutil.move(source_file_path, destination_file_path)
                current_time = datetime.datetime.now()
                print(f"{current_time}: Moved '{file_name}'")

    @staticmethod
    def delete_folder(folder_path):
        shutil.rmtree(folder_path)

class MegaDownload:
    def __init__(self, public_link, target_folder, max_download_time):
        current_time = datetime.datetime.now()
        print(f"####################################### Megadownload job started at {current_time} #######################################")
        self.public_link = public_link
        self.target_folder = target_folder
        self.max_download_time = max_download_time
        self.tmp_folder = FileUtils.create_tmp_folder()
        self._login()

    def __del__(self):
        self._logout()
        FileUtils.delete_folder(self.tmp_folder)
        current_time = datetime.datetime.now()
        print(f"####################################### Megadownload job ended at {current_time} #######################################")

    def _login(self):
        p = pexpect.spawn(f"mega-login {self.public_link}")
        p.expect(pexpect.EOF)
        print('Logged in to: ', self.public_link)

    def _logout(self):
        p = pexpect.spawn('mega-logout')
        p.expect(pexpect.EOF)
        print('Logged out')

    @staticmethod
    def is_logged_in():
        p = pexpect.spawn('mega-ls')
        return (p.wait() == 0)


    def _mega_get(self, link):
        command = f"mega-get {link} {self.tmp_folder}"
        print('command: ', command)
        get = pexpect.spawn(command, timeout=self.max_download_time)
        output = ''
        timeout_exceeded = False
        quota_exceeded = False

        status = DownloadStatus.NO_ERROR

        try:
            output = get.read().decode()
        except KeyboardInterrupt:
            sys.exit(1)
        except Exception as e:
            current_time = datetime.datetime.now()
            status = DownloadStatus.TIMEOUT_EXCEEDED
            print(f"Timeout exceeded for downloading file at {current_time}")

        get.close()

        if (status == DownloadStatus.NO_ERROR) and (get.exitstatus != 0):
            if get.exitstatus == 11:
                status = DownloadStatus.QUOTA_EXCEEDED
            else:
                status = DownloadStatus.OTHER_MEGA_GET_ERROR

        print('mega-get finished with status: ', status, ' ', get.exitstatus)
        return (output, status)

    def _get_dwllink_and_file_name(self):
        p = pexpect.spawn('mega-find *')
        p.expect(pexpect.EOF)
        mega_find_output = p.before.decode().strip()
        print('Listed files')
        dwllink_and_file_name = []
        entries = mega_find_output.split('\n')
        for entry in entries:
            entry = entry.replace('\r','')
            if entry.endswith('.mkv') or entry.endswith('.mp4'):
                split_entry = entry.split('/')
                download_link = os.path.join(*split_entry)
                posix_path = shlex.quote(download_link)
                file_name = split_entry[-1]
                dwllink_and_file_name.append((posix_path, file_name))
        return dwllink_and_file_name

    def _get_download_links_of_missing_files(self, dwllink_and_file_name):
        download_links = []
        for download_link, file_name in dwllink_and_file_name:
            if not FileUtils.folder_contains_file(self.target_folder, file_name):
                print('File missing: ', file_name)
                download_links.append(download_link)
        if not download_links:
            print('No file is missing')
        return download_links

    def download_files(self):
        status = DownloadStatus.NO_ERROR
        dwllink_and_file_name = self._get_dwllink_and_file_name()
        while True:
            download_links = self._get_download_links_of_missing_files(dwllink_and_file_name)
            if not download_links:
                break

            unexpected_error = False
            for link in download_links:
                self._logout()
                Fritzbox.change_ip_address()
                self._login()
                output, status = self._mega_get(link)
                if status == DownloadStatus.TIMEOUT_EXCEEDED:
                    FileUtils.remove_mega_tmp_files(self.tmp_folder)
                elif status == DownloadStatus.NO_ERROR:
                    FileUtils.move_files_to_destination(self.tmp_folder, self.target_folder)
                else:
                    unexpected_error = True
                    break

            if unexpected_error:
                current_time = datetime.datetime.now()
                print(f"####################################### {current_time} Unexpected error encountered, aborting...  #######################################")
                break

        return status
