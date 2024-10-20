from cbox.model import CboxInfo, FanStatus
from aiohttp import ClientSession, ClientResponse
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)


class Cbox:

    class Status(Enum):
        ON = 'on'
        OFF = 'off'

    def __init__(self, client: ClientSession) -> None:
        self.path: str = "/cgi-bin/sendmsg.lua"
        self.client_session = client

    async def __aenter__(self) -> None:
        return self

    async def __aexit__(self, exc_type, exc_value, exc_tb) -> None:
        await self.client_session.close()

    def connected_to(host: str) -> 'Cbox':
        """Return a Cbox connected to given host"""
        return Cbox(ClientSession(f"http://{host}/"))

    async def fetch_info(self) -> CboxInfo:
        """Fetch all the general info in one call"""
        logger.debug("Fetch infos")
        async with self.client_session.get(self.path, params=[('cmd', 'GET ALLS')]) as response:
            if response.status != 200:
                raise Exception('Can\'t fetch infos')
            response_json = await response.json()
            if response_json['SUCCESS'] is not True:
                raise Exception('Requet response is not SUCCESS')
            return CboxInfo.from_dict(response_json)

    async def change_status(self, status: Status) -> None:
        """Turn on/off the device"""
        logger.debug(f"Change status => {status.value}")
        async with self.client_session.get(self.path, params=[('cmd', f"CMD {status.value}")]) as response:
            await Cbox.check_response_success(response)

    async def change_temperature_setpoint(self, temperature: int) -> None:
        """Change temperature setpoint"""
        logger.debug(f"Change temperature setpoint => {temperature}")
        if not 11 < temperature < 51:
            raise Exception(
                'Unexpected temperature, should be between 12 and 50')
        async with self.client_session.get(self.path, params=[('cmd', f"SET SETP {temperature}")]) as response:
            await Cbox.check_response_success(response)

    async def change_power_setpoint(self, power: int) -> None:
        """Change power setpoint"""
        logger.debug(f"Change power setpoing => {power}")
        if not 1 <= power <= 5:
            logger.warning(f"Invalid power value {power}, value should be between 1-5")
            raise "Unexpected power, should be between 1 and 5"
        async with self.client_session.get(self.path, params=[('cmd', f"SET POWR {power}")]) as response:
            await Cbox.check_response_success(response)

    async def change_fan_setpoint(self, fan_status: FanStatus) -> None:
        """Change fan setpoint"""
        logger.debug(f"Change fan setpoint {fan_status.name}")
        async with self.client_session.get(self.path, params=[('cmd', f"SET RFAN {fan_status.value}")]) as response:
            await Cbox.check_response_success(response)

    async def check_response_success(response: ClientResponse):
        if response.status != 200:
            raise Exception(f'Got unexpected response status {
                            response.status}')
        response_json = await response.json()
        if response_json['SUCCESS'] is not True:
            raise Exception(f'Requet response is not SUCCESS => {
                            json.dumps(response_json)}')
