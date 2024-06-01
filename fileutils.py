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

import random
import tempfile
import os
import shutil
import string
from datetime import datetime

class FileUtils:
    def __init__(self):
        pass

    @staticmethod
    def does_folder_exist(folder_path):
        exists = True
        if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
            exists = False
        return exists

    @staticmethod
    def create_tmp_folder():
        tmp_folder_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))
        tmp_dir = tempfile.gettempdir()
        tmp_folder_path = os.path.join(tmp_dir, tmp_folder_name)
        os.mkdir(tmp_folder_path)
        return tmp_folder_path

    @staticmethod
    def remove_mega_tmp_files(folder_path):
        for filename in os.listdir(folder_path):
            if filename.startswith('.'):
                file_path = os.path.join(folder_path, filename)
                os.remove(file_path)

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
                shutil.move(source_file_path, destination_file_path)

    @staticmethod
    def delete_folder(folder_path):
        shutil.rmtree(folder_path)
