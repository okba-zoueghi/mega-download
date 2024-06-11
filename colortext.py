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

def color_text(text, color):
    # ANSI escape codes for colors
    COLORS = {
        "BLACK": "\033[90m",
        "RED": "\033[91m",
        "GREEN": "\033[92m",
        "YELLOW": "\033[93m",
        "BLUE": "\033[94m",
        "MAGENTA": "\033[95m",
        "CYAN": "\033[96m",
        "WHITE": "\033[97m",
        "RESET": "\033[0m"
    }
    # Check if the color is supported
    if color.upper() not in COLORS:
        raise ValueError(f"Unsupported color: {color}")
    # Get the ANSI escape code for the color
    color_code = COLORS[color.upper()]
    # Return the colored text
    return f"{color_code}{text}{COLORS['RESET']}"

def print_progress_bar(percentage, length=50):
    filled_length = int(length * percentage // 100)
    bar = '█' * filled_length + '-' * (length - filled_length)
    print(f'\r|{bar}| {percentage:.1f}% Complete', end='')
