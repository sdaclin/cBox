import json
import logging
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Self

from aiohttp import ClientResponse, ClientSession

logger = logging.getLogger(__name__)


class StoveStatus(Enum):
    OFF = 0
    OFF_TIMER = 1
    TESTFIRE = 2
    HEATUP = 3
    FUELIGN = 4
    IGNTEST = 5
    BURNING = 6
    COOLFLUID = 9
    FIRESTOP = 10
    CLEANFIRE = 11
    COOL = 12
    CHIMNEY_ALARM = 241
    GRATE_ERROR = 243
    NTC2_ALARM = 244
    NTC3_ALARM = 245
    DOOR_ALARM = 247
    PRESS_ALARM = 248
    NTC1_ALARM = 249
    TC1_ALARM = 250
    GAS_ALARM = 252
    NOPELLET_ALAR = 253


class FanStatus(Enum):
    OFF = 0
    SPEED_1 = 1
    SPEED_2 = 2
    SPEED_3 = 3
    SPEED_4 = 4
    SPEED_5 = 5
    HIGH = 6
    AUTO = 7


@dataclass
class CboxInfo:
    """Class for keeping track of Cbox info as returned by the cBox API"""

    timestamp: datetime = datetime.now()

    mac: str = "00:00:00:00:00:00"

    status: StoveStatus = StoveStatus.OFF

    fanSetpoint: FanStatus = FanStatus.OFF
    powerSetpoint: int = 1
    temperatureSetpoint: int = 19

    t1: int = 0
    t2: int = 0
    t3: int = 0
    t4: int = 0
    t5: int = 0

    pelletQttyTotalKg: int = 0

    firmwareVersion: int = 0
    firmwareDate: date = date.today()

    def __repr__(self) -> str:
        return json.dumps(
            {
                "timestamp": str(self.timestamp),
                "mac": self.mac,
                "globalStatus": self.status.name,
                "fanSetpoint": self.fanSetpoint.name,
                "powerSetpoint": self.powerSetpoint,
                "temperatureSetpoint": self.temperatureSetpoint,
                "temperature1": self.t1,
                "temperature2": self.t2,
                "temperature3": self.t3,
                "temperature4": self.t4,
                "temperature5": self.t5,
                "pelletQttyTotalKg": self.pelletQttyTotalKg,
                "firmwareDate": str(self.firmwareDate),
                "firmwareVersion": self.firmwareVersion,
            }
        )

    def from_dict(dict: dict) -> Self:
        return CboxInfo(
            timestamp=datetime.fromtimestamp(dict["INFO"]["TS"]),
            mac=dict["DATA"]["MAC"],
            status=StoveStatus(dict["DATA"]["STATUS"]),
            fanSetpoint=FanStatus(dict["DATA"]["F2L"]),
            powerSetpoint=dict["DATA"]["PWR"],
            temperatureSetpoint=dict["DATA"]["SETP"],
            t1=dict["DATA"]["T1"],
            t2=dict["DATA"]["T2"],
            t3=dict["DATA"]["T3"],
            t4=dict["DATA"]["T4"],
            t5=dict["DATA"]["T5"],
            pelletQttyTotalKg=dict["DATA"]["PQT"],
            firmwareVersion=int(dict["DATA"]["VER"]),
            firmwareDate=date.fromisoformat(dict["DATA"]["FWDATE"]),
        )


class Cbox:
    class Status(Enum):
        ON = "on"
        OFF = "off"

    def __init__(self, client: ClientSession) -> None:
        self.path: str = "/cgi-bin/sendmsg.lua"
        self.client_session = client

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type, exc_value, exc_tb) -> None:
        await self.client_session.close()

    @classmethod
    def connected_to(cls, host: str) -> Self:
        """Return a Cbox connected to given host"""
        return cls(ClientSession(f"http://{host}/"))

    async def fetch_info(self) -> CboxInfo:
        """Fetch all the general info in one call"""
        logger.debug("Fetch infos")
        async with self.client_session.get(self.path, params=[("cmd", "GET ALLS")]) as response:
            if response.status != 200:
                raise Exception("Can't fetch infos")
            response_json = await response.json()
            if response_json["SUCCESS"] is not True:
                raise Exception("Request response is not SUCCESS")
            return CboxInfo.from_dict(response_json)

    async def get_info(self, cmd: str) -> None:
        """Fetch cmd"""
        logger.debug(f"Fetch cmd {cmd}")
        async with self.client_session.get(self.path, params=[("cmd", f"GET {cmd}")]) as response:
            if response.status != 200:
                raise Exception(f"Can't fetch {cmd}")
            response_json = await response.json()
            if response_json["SUCCESS"] is not True:
                raise Exception("Request response is not SUCCESS")
            return response_json

    async def bkp(self) -> None:
        """Backup cmd"""
        cmd = "BKP PARM JSON"
        logger.debug(f"Backp cmd {cmd}")
        async with self.client_session.get(self.path, params=[("cmd", f"{cmd}")]) as response:
            if response.status != 200:
                raise Exception(f"Can't fetch {cmd}")
            response_json = await response.json()
            if response_json["SUCCESS"] is not True:
                raise Exception("Request response is not SUCCESS")
            return response_json

    async def power_on(self) -> None:
        """Turn on the device"""
        logger.debug("Power on")
        async with self.client_session.get(self.path, params=[("cmd", "CMD on")]) as response:
            await Cbox._check_response_success(response)

    async def power_off(self) -> None:
        """Turn off the device"""
        logger.debug("Power off")
        async with self.client_session.get(self.path, params=[("cmd", "CMD off")]) as response:
            await Cbox._check_response_success(response)

    async def change_temperature_setpoint(self, temperature: int) -> None:
        """Change temperature setpoint"""
        logger.debug(f"Change temperature setpoint => {temperature}")
        if not 11 < temperature < 51:
            raise Exception("Unexpected temperature, should be between 12 and 50")
        async with self.client_session.get(self.path, params=[("cmd", f"SET SETP {temperature}")]) as response:
            await Cbox._check_response_success(response)

    async def change_power_setpoint(self, power: int) -> None:
        """Change power setpoint"""
        logger.debug(f"Change power setpoint => {power}")
        if not 1 <= power <= 5:
            logger.warning(f"Invalid power value {power}, value should be between 1-5")
            raise "Unexpected power, should be between 1 and 5"
        async with self.client_session.get(self.path, params=[("cmd", f"SET POWR {power}")]) as response:
            await Cbox._check_response_success(response)

    async def change_fan_setpoint(self, fan_status: FanStatus) -> None:
        """Change fan setpoint"""
        logger.debug(f"Change fan setpoint {fan_status.name}")
        async with self.client_session.get(self.path, params=[("cmd", f"SET RFAN {fan_status.value}")]) as response:
            await Cbox._check_response_success(response)

    async def _check_response_success(response: ClientResponse):
        if response.status != 200:
            raise Exception(f"Got unexpected response status {response.status}")
        response_json = await response.json()
        if response_json["SUCCESS"] is not True:
            raise Exception(f"Request response is not SUCCESS => {json.dumps(response_json)}")
