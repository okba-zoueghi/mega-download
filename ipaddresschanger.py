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

import logging
import random
import time
from fritzbox.fritzbox import Fritzbox, RequestError
from pyglinet.glinet import GlInet

"""
Possible value are 'Fritzbox' or 'GlInet'
If left empty or set to another value, by default GlInet will used
"""
ROUTER = 'GlInet'

"""
GlInet router password
"""
GLINET_PASSWORD = 'your router password'

"""
Name of VPN provider for glinet router
"""
VPN_PROVIDER = 'Mullvad'

class ChangeIpException(Exception):
    def __init__(self, message):
        super().__init__(message)

class IpChangerFritzbox:
    def __init__(self):
        self.fritzbox = Fritzbox('http://fritz.box:49000')

    def change_ip(self):
        print('Current IP: ', self.fritzbox.get_public_ip())
        print('Changing IP address...')
        change_ip_error_code = self.fritzbox.change_ip_address_block()
        if change_ip_error_code != RequestError.NO_ERROR:
            raise ChangeIpException(f'Failed to change ip with error: {change_ip_error_code}')
        print('New IP: ', self.fritzbox.get_public_ip())

class IpChangerGlinet:
    def __init__(self, glinet_password, vpn_provider):
        self.password = glinet_password
        self.vpn_provider = vpn_provider

    def change_ip(self):
        logging.getLogger('glinet').setLevel(logging.CRITICAL)
        glinet = GlInet(password=self.password, keep_alive=False)
        glinet.login()
        api_client = glinet.get_api_client()
        groups = api_client.wg_client.get_group_list()['groups']
        group_id = None
        for group in groups:
            if group['group_name'] == self.vpn_provider:
                group_id = group['group_id']
        if not group_id:
            raise ChangeIpException(f'Failed to change ip with error: {self.vpn_provider} not found as vpn provider')
        peers = api_client.wg_client.get_config_list({'group_id': group_id})['peers']
        while True:
            api_client.wg_client.stop()
            random_peer = random.choice(peers)
            api_client.wg_client.start({'group_id': group_id, 'peer_id': random_peer['peer_id']})
            print('Connecting to VPN server...')
            time.sleep(10)
            current_vpn_connection_status = api_client.wg_client.get_status()['status']
            if current_vpn_connection_status == 1:
                print(f"Connected to VPN server {random_peer['name']} with ip {api_client.wg_client.get_status()['domain']}")
                break
            print(f"Connecting to VPN server {random_peer['name']} failed")
            print('Selecting another random server...')
        glinet.logout()

    def __del__(self):
        logging.getLogger('glinet').setLevel(logging.CRITICAL)
        glinet = GlInet(password=self.password, keep_alive=False)
        glinet.login()
        api_client = glinet.get_api_client()
        api_client.wg_client.stop()
        print(f"Stopped the connection to the VPN server ({api_client.wg_client.get_status()['domain']})")
        glinet.logout()


def get_ip_changer():
    if ROUTER == 'Fritzbox':
        return IpChangerFritzbox()
    return IpChangerGlinet(GLINET_PASSWORD, VPN_PROVIDER)
