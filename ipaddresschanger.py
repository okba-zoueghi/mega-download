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
import json

from fritzbox.fritzbox import Fritzbox, RequestError
from spawnhelper import SpawnHelper, SpawnStatus
from colortext import color_text

class ChangeIpException(Exception):
    def __init__(self, message):
        super().__init__(message)


class Glinet:
    def __init__(self, glinet_password):
        self.ip = "192.168.8.1"
        self.password = glinet_password

    @staticmethod
    def send_request(command):
        response = None
        spawn_status, process_exit_code, output = SpawnHelper.spawn(command)
        if spawn_status == SpawnStatus.NO_ERROR:
            if process_exit_code != 0:
                print(color_text(f"Output of {command}:\n[{output}]", "RED"))
                raise ChangeIpException(f"The command '{command}' failed")
            else:
                response = json.loads(output)
        elif spawn_status == SpawnStatus.TIMEOUT:
            print(color_text(f"Output of {command}:\n[{output}]", "RED"))
            raise ChangeIpException(f"The command '{command}' failed due to timeout")
        else:
            print(color_text(f"Output of {command}:\n[{output}]", "RED"))
            raise ChangeIpException(f"The command '{command}' failed due to unexpected error")
        return response

    def get_wireguard_group_list(self):
        json_payload = '{\\\"module\\\":\\\"wg-client\\\",\\\"func\\\":\\\"get_group_list\\\",\\\"params\\\":{}}'
        command = f"sshpass -p '{self.password}' ssh root@{self.ip} ubus call gl-session call '{json_payload}'"
        group_list = Glinet.send_request(command)
        return group_list["result"]

    def get_wireguard_group_config_list(self, group_id):
        json_payload = f'{{\\\"module\\\":\\\"wg-client\\\",\\\"func\\\":\\\"get_config_list\\\",\\\"params\\\":{{\\\"group_id\\\":{group_id}}}}}'
        command = f"sshpass -p '{self.password}' ssh root@{self.ip} ubus call gl-session call '{json_payload}'"
        config_list = Glinet.send_request(command)
        return config_list["result"]

    def wireguard_stop(self):
        json_payload = '{\\\"module\\\":\\\"vpn-client\\\",\\\"func\\\":\\\"set_tunnel\\\",\\\"params\\\":{\\\"enabled\\\":false,\\\"tunnel_id\\\":10}}'
        command = f"sshpass -p '{self.password}' ssh root@{self.ip} ubus call gl-session call '{json_payload}'"
        Glinet.send_request(command)

    def wireguard_start(self, group_id, peer_id):
        json_payload = f'{{\\\"module\\\":\\\"vpn-client\\\",\\\"func\\\":\\\"set_tunnel\\\",\\\"params\\\":{{\\\"via\\\":{{\\\"type\\\":\\\"wireguard\\\",\\\"group_id\\\":{group_id},\\\"peer_id\\\":{peer_id}}},\\\"isTapS2s\\\":false,\\\"tunnel_id\\\":10}}}}'
        command = f"sshpass -p '{self.password}' ssh root@{self.ip} ubus call gl-session call '{json_payload}'"
        set_server = Glinet.send_request(command)
        time.sleep(2)
        json_payload = '{\\\"module\\\":\\\"vpn-client\\\",\\\"func\\\":\\\"set_tunnel\\\",\\\"params\\\":{\\\"enabled\\\":true,\\\"tunnel_id\\\":10}}'
        command = f"sshpass -p '{self.password}' ssh root@{self.ip} ubus call gl-session call '{json_payload}'"
        start = Glinet.send_request(command)

    def get_wireguard_status(self):
        json_payload = '{\\\"module\\\":\\\"vpn-client\\\",\\\"func\\\":\\\"get_status\\\",\\\"params\\\":{}}'
        command = f"sshpass -p '{self.password}' ssh root@{self.ip} ubus call gl-session call '{json_payload}'"
        status = Glinet.send_request(command)
        return status["result"]["status_list"][0]


class IpChangerFritzbox:
    def __init__(self):
        self.fritzbox = Fritzbox("http://fritz.box:49000")

    def change_ip(self):
        print("Current IP: ", self.fritzbox.get_public_ip())
        print("Changing IP address...")
        change_ip_error_code = self.fritzbox.change_ip_address_block()
        if change_ip_error_code != RequestError.NO_ERROR:
            raise ChangeIpException(
                f"Failed to change ip with error: {change_ip_error_code}"
            )
        print("New IP: ", self.fritzbox.get_public_ip())


class IpChangerGlinet:
    def __init__(self, glinet_password, vpn_provider):
        self.password = glinet_password
        self.vpn_provider = vpn_provider

    def change_ip(self):
        glinet = Glinet(self.password)
        groups = glinet.get_wireguard_group_list()["groups"]
        group_id = None
        for group in groups:
            if group["group_name"] == self.vpn_provider:
                group_id = group["group_id"]
        if not group_id:
            raise ChangeIpException(f"Failed to change ip with error: {self.vpn_provider} not found as vpn provider")
        peers = glinet.get_wireguard_group_config_list(group_id)["peers"]
        while True:
            glinet.wireguard_stop()
            random_peer = random.choice(peers)
            glinet.wireguard_start(group_id, random_peer["peer_id"])
            print("Connecting to VPN server...")
            time.sleep(10)
            current_vpn_connection_status = glinet.get_wireguard_status()["status"]
            if current_vpn_connection_status == 1:
                print(f"Connected to VPN server {random_peer['name']} with ip {glinet.get_wireguard_status()['domain'][0]}")
                break
            print(f"Connecting to VPN server {random_peer['name']} failed")
            print("Selecting another random server...")

    def __del__(self):
        glinet = Glinet(self.password)
        glinet.wireguard_stop()
        print(f"Stopped the connection to the VPN server ({glinet.get_wireguard_status()['domain'][0]})")

class IpChangerHelper:
    router = None
    password = None
    vpn_provider = None

    def __init__(self):
        pass

    @staticmethod
    def set_router(router):
        IpChangerHelper.router = router

    @staticmethod
    def set_glinet_config(password,vpn_provider):
        IpChangerHelper.password = password
        IpChangerHelper.vpn_provider = vpn_provider

    @staticmethod
    def get_ip_changer():
        if IpChangerHelper.router == 'fritzbox':
            return IpChangerFritzbox()
        elif IpChangerHelper.router == 'glinet':
            return IpChangerGlinet(IpChangerHelper.password, IpChangerHelper.vpn_provider)
