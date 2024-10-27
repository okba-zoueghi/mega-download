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
from enum import Enum

class SpawnStatus(Enum):
    NO_ERROR = 0
    TIMEOUT = 1
    UNEXPECTED_ERROR = 100


class SpawnHelper:
    def __init__(self):
        pass

    @staticmethod
    def spawn(command,timeout=30):
        spawn_status = SpawnStatus.NO_ERROR
        output = ''
        p = pexpect.spawn(command, timeout=timeout)
        try:
            output = p.read().decode()
        except pexpect.TIMEOUT as e:
            spawn_status = SpawnStatus.TIMEOUT
            print(f'Spawn failed due to timeout: {e}')
        except Exception as e:
            spawn_status = SpawnStatus.UNEXPECTED_ERROR
            print(f'Spawn failed: {e}')
        p.close()
        process_exit_code = p.exitstatus
        return (spawn_status, process_exit_code, output)
