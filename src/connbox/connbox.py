import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Self

from aiohttp import ClientError, ClientSession, ClientTimeout

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT: float = 10
ALARM_STATUS_THRESHOLD: int = 241


class CboxError(Exception):
    """Base exception for all cBox errors"""


class CboxConnectionError(CboxError):
    """The cBox can't be reached or returned an unexpected HTTP response"""


class CboxCommandError(CboxError):
    """The cBox answered but rejected the command"""


class StoveStatus(Enum):
    UNKNOWN = -1
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

    @classmethod
    def _missing_(cls, value: object) -> Self:
        logger.warning(f"Unknown stove status {value}")
        return cls.UNKNOWN


class FanStatus(Enum):
    UNKNOWN = -1
    OFF = 0
    SPEED_1 = 1
    SPEED_2 = 2
    SPEED_3 = 3
    SPEED_4 = 4
    SPEED_5 = 5
    HIGH = 6
    AUTO = 7

    @classmethod
    def _missing_(cls, value: object) -> Self:
        logger.warning(f"Unknown fan status {value}")
        return cls.UNKNOWN


@dataclass
class CboxInfo:
    """Class for keeping track of Cbox info as returned by the cBox API"""

    timestamp: datetime = field(default_factory=datetime.now)

    mac: str = "00:00:00:00:00:00"

    status: StoveStatus = StoveStatus.OFF

    fanSetpoint: FanStatus = FanStatus.OFF
    powerSetpoint: int = 1
    temperatureSetpoint: int = 19

    t1: float = 0
    t2: float = 0
    t3: float = 0
    t4: float = 0
    t5: float = 0

    pelletQttyTotalKg: int = 0

    firmwareVersion: int = 0
    firmwareDate: date = field(default_factory=date.today)

    rawStatus: int = 0
    """Status code as sent by the device, useful when status is UNKNOWN"""

    @property
    def is_alarm(self) -> bool:
        return self.rawStatus >= ALARM_STATUS_THRESHOLD

    def __repr__(self) -> str:
        return json.dumps(
            {
                "timestamp": str(self.timestamp),
                "mac": self.mac,
                "globalStatus": self.status.name,
                "rawStatus": self.rawStatus,
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

    @staticmethod
    def from_dict(response: dict) -> "CboxInfo":
        data = response["DATA"]
        return CboxInfo(
            timestamp=datetime.fromtimestamp(response["INFO"]["TS"]),
            mac=data["MAC"],
            status=StoveStatus(data["STATUS"]),
            fanSetpoint=FanStatus(data["F2L"]),
            powerSetpoint=data["PWR"],
            temperatureSetpoint=data["SETP"],
            t1=data["T1"],
            t2=data["T2"],
            t3=data["T3"],
            t4=data["T4"],
            t5=data["T5"],
            pelletQttyTotalKg=data["PQT"],
            firmwareVersion=int(data["VER"]),
            firmwareDate=date.fromisoformat(data["FWDATE"]),
            rawStatus=data["STATUS"],
        )


class Cbox:
    PATH: str = "/cgi-bin/sendmsg.lua"

    def __init__(self, client: ClientSession, host: str | None = None, timeout: float = DEFAULT_TIMEOUT) -> None:
        """Build a Cbox using the given session.

        When `host` is given, requests target `http://{host}`, so any session can be used (it won't be closed).
        Otherwise the session is expected to be configured with the cBox base url.
        """
        self.client_session = client
        self.url: str = f"http://{host}{Cbox.PATH}" if host else Cbox.PATH
        self.timeout = ClientTimeout(total=timeout)
        self._owns_session = False

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type, exc_value, exc_tb) -> None:
        await self.close()

    async def close(self) -> None:
        """Close the underlying session, only if it was created by this Cbox"""
        if self._owns_session:
            await self.client_session.close()

    @classmethod
    def connected_to(cls, host: str, timeout: float = DEFAULT_TIMEOUT) -> Self:
        """Return a Cbox connected to given host, owning its own session"""
        cbox = cls(ClientSession(), host, timeout)
        cbox._owns_session = True
        return cbox

    async def fetch_info(self) -> CboxInfo:
        """Fetch all the general info in one call"""
        logger.debug("Fetch infos")
        response_json = await self._send("GET ALLS")
        try:
            return CboxInfo.from_dict(response_json)
        except (KeyError, TypeError, ValueError) as err:
            raise CboxCommandError(f"Unexpected GET ALLS response => {json.dumps(response_json)}") from err

    async def get_info(self, cmd: str) -> dict[str, Any]:
        """Fetch cmd"""
        logger.debug(f"Fetch cmd {cmd}")
        return await self._send(f"GET {cmd}")

    async def bkp(self) -> dict[str, Any]:
        """Backup cmd"""
        logger.debug("Backup cmd")
        return await self._send("BKP PARM JSON")

    async def power_on(self) -> None:
        """Turn on the device"""
        logger.debug("Power on")
        await self._send("CMD on")

    async def power_off(self) -> None:
        """Turn off the device"""
        logger.debug("Power off")
        await self._send("CMD off")

    async def change_temperature_setpoint(self, temperature: int) -> None:
        """Change temperature setpoint"""
        logger.debug(f"Change temperature setpoint => {temperature}")
        if not 12 <= temperature <= 50:
            raise ValueError(f"Unexpected temperature {temperature}, should be between 12 and 50")
        await self._send(f"SET SETP {temperature}")

    async def change_power_setpoint(self, power: int) -> None:
        """Change power setpoint"""
        logger.debug(f"Change power setpoint => {power}")
        if not 1 <= power <= 5:
            raise ValueError(f"Unexpected power {power}, should be between 1 and 5")
        await self._send(f"SET POWR {power}")

    async def change_fan_setpoint(self, fan_status: FanStatus) -> None:
        """Change fan setpoint"""
        logger.debug(f"Change fan setpoint {fan_status.name}")
        if fan_status is FanStatus.UNKNOWN:
            raise ValueError("Can't set fan setpoint to UNKNOWN")
        await self._send(f"SET RFAN {fan_status.value}")

    async def _send(self, cmd: str) -> dict[str, Any]:
        try:
            async with self.client_session.get(self.url, params=[("cmd", cmd)], timeout=self.timeout) as response:
                if response.status != 200:
                    raise CboxConnectionError(f"Got unexpected response status {response.status} for {cmd}")
                response_json = await response.json(content_type=None)
        except (ClientError, TimeoutError, asyncio.TimeoutError, json.JSONDecodeError) as err:
            raise CboxConnectionError(f"Error while sending {cmd}: {err!r}") from err
        if not isinstance(response_json, dict) or response_json.get("SUCCESS") is not True:
            raise CboxCommandError(f"Request response is not SUCCESS => {json.dumps(response_json)}")
        return response_json
