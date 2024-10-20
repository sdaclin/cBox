import pytest
import asyncio

from aiohttp import web

from cbox.connbox import Cbox

from tests.connbox_simulator import CboxSimulator

from datetime import datetime, date
from cbox.model import CboxInfo, StoveStatus, FanStatus


@pytest.fixture
def simulator() -> CboxSimulator:
    return CboxSimulator()


@pytest.fixture
async def cbox(simulator: CboxSimulator, aiohttp_client) -> Cbox:
    client = await aiohttp_client(simulator.app())
    return Cbox(client)


async def test_cbox_should_fetch_infos(cbox: Cbox):
    res = await cbox.fetch_info()
    assert res == CboxInfo(datetime(2024, 10, 12, 11, 30, 54),
                           StoveStatus.OFF, FanStatus.OFF, 1, 19, 24.8, 0, 133, 0, 49, 48, date(2023, 7, 26))

async def test_cbox_should_change_status(cbox: Cbox):
    await cbox.change_status(Cbox.Status.ON) # Only the simulator directly switch from OFF to BURNING
    assert (await cbox.fetch_info()).status == StoveStatus.BURNING

    await cbox.change_status(Cbox.Status.OFF) # Only the simulator directly switch from BURNING to OFF
    assert (await cbox.fetch_info()).status == StoveStatus.OFF

async def test_cbox_should_change_temperature_setpoint(cbox:Cbox):
    await cbox.change_temperature_setpoint(19)
    assert (await cbox.fetch_info()).temperatureSetpoint == 19

    await cbox.change_temperature_setpoint(16)
    assert (await cbox.fetch_info()).temperatureSetpoint == 16

async def test_cbox_should_change_power_setpoint(cbox:Cbox):
    await cbox.change_power_setpoint(5)
    assert (await cbox.fetch_info()).powerSetpoint == 5

    await cbox.change_power_setpoint(1)
    assert (await cbox.fetch_info()).powerSetpoint == 1

async def test_cbox_should_change_fan_setpoint(cbox:Cbox):
    await cbox.change_fan_setpoint(FanStatus.HIGH)
    assert (await cbox.fetch_info()).fanSetpoint == FanStatus.HIGH

    await cbox.change_fan_setpoint(FanStatus.SPEED_3)
    assert (await cbox.fetch_info()).fanSetpoint == FanStatus.SPEED_3


