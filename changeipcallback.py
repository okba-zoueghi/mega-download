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

from fritzbox.fritzbox import Fritzbox, RequestError

class ChangeIpException(Exception):
    def __init__(self, message):
        super().__init__(message)

def change_ip_address():
    """
    This function is used as a callback to change the IP address in the class MegaDownload.
    Update the implementation this function to change the ip address of your router.
    The function shall block until the ip address is changed.
    If the function fails to change the ip address, the exception ChangeIpException shall be raised.
    """
    fritzbox = Fritzbox('http://fritz.box:49000')
    print('Current IP: ', fritzbox.get_public_ip())
    print('Changing IP address...')
    change_ip_error_code = fritzbox.change_ip_address_block()
    if change_ip_error_code != RequestError.NO_ERROR:
        raise ChangeIpException(f'Failed to change ip with error: {change_ip_error_code}')
    print('New IP: ', fritzbox.get_public_ip())
