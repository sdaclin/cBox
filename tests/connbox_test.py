from datetime import date, datetime

import pytest
from aiohttp import ClientSession

from connbox import Cbox, CboxCommandError, CboxConnectionError, CboxInfo, FanStatus, StoveStatus
from tests.connbox_simulator import CboxSimulator


@pytest.fixture
def simulator() -> CboxSimulator:
    return CboxSimulator()


@pytest.fixture
async def cbox(simulator: CboxSimulator, aiohttp_client) -> Cbox:
    client = await aiohttp_client(simulator.app())
    return Cbox(client)


async def test_cbox_should_fetch_infos(cbox: Cbox):
    res = await cbox.fetch_info()
    assert res == CboxInfo(
        datetime.fromtimestamp(1728725454),
        "FF:FF:FF:FF:FF:FF",
        StoveStatus.OFF,
        FanStatus.OFF,
        1,
        19,
        24.8,
        0,
        133,
        0,
        49,
        42,
        48,
        date(2023, 7, 26),
    )


async def test_cbox_should_power_on(cbox: Cbox):
    await cbox.power_on()  # Only the simulator directly switch from OFF to BURNING
    assert (await cbox.fetch_info()).status == StoveStatus.BURNING

    await cbox.power_off()  # Only the simulator directly switch from BURNING to OFF
    assert (await cbox.fetch_info()).status == StoveStatus.OFF


async def test_cbox_should_change_temperature_setpoint(cbox: Cbox):
    await cbox.change_temperature_setpoint(19)
    assert (await cbox.fetch_info()).temperatureSetpoint == 19

    await cbox.change_temperature_setpoint(16)
    assert (await cbox.fetch_info()).temperatureSetpoint == 16


async def test_cbox_should_change_power_setpoint(cbox: Cbox):
    await cbox.change_power_setpoint(5)
    assert (await cbox.fetch_info()).powerSetpoint == 5

    await cbox.change_power_setpoint(1)
    assert (await cbox.fetch_info()).powerSetpoint == 1


async def test_cbox_should_change_fan_setpoint(cbox: Cbox):
    await cbox.change_fan_setpoint(FanStatus.HIGH)
    assert (await cbox.fetch_info()).fanSetpoint == FanStatus.HIGH

    await cbox.change_fan_setpoint(FanStatus.SPEED_3)
    assert (await cbox.fetch_info()).fanSetpoint == FanStatus.SPEED_3


async def test_cbox_should_get_info(cbox: Cbox):
    res = await cbox.get_info("ALLS")
    assert res["SUCCESS"]


async def test_cbox_should_tolerate_unknown_status(simulator: CboxSimulator, cbox: Cbox):
    simulator.status_code_override = 42
    res = await cbox.fetch_info()
    assert res.status == StoveStatus.UNKNOWN
    assert res.rawStatus == 42
    assert not res.is_alarm


async def test_cbox_should_flag_alarm(simulator: CboxSimulator, cbox: Cbox):
    simulator.status_code_override = StoveStatus.NOPELLET_ALAR.value
    res = await cbox.fetch_info()
    assert res.status == StoveStatus.NOPELLET_ALAR
    assert res.is_alarm


async def test_cbox_should_reject_invalid_power(cbox: Cbox):
    with pytest.raises(ValueError):
        await cbox.change_power_setpoint(6)


async def test_cbox_should_reject_invalid_temperature(cbox: Cbox):
    with pytest.raises(ValueError):
        await cbox.change_temperature_setpoint(11)


async def test_cbox_should_raise_command_error_when_not_success(cbox: Cbox):
    with pytest.raises(CboxCommandError):
        await cbox._send("SET POWR 9")


async def test_cbox_should_raise_connection_error_on_bad_http_status(cbox: Cbox):
    with pytest.raises(CboxConnectionError):
        await cbox._send("UNKNOWN CMD")


async def test_cbox_should_raise_connection_error_when_unreachable(unused_tcp_port: int):
    async with Cbox.connected_to(f"127.0.0.1:{unused_tcp_port}", timeout=2) as cbox:
        with pytest.raises(CboxConnectionError):
            await cbox.fetch_info()


async def test_cbox_should_use_external_session_without_closing_it(simulator: CboxSimulator, aiohttp_server):
    server = await aiohttp_server(simulator.app())
    async with ClientSession() as session:
        async with Cbox(session, f"{server.host}:{server.port}") as cbox:
            await cbox.change_power_setpoint(3)
            assert (await cbox.fetch_info()).powerSetpoint == 3
        assert not session.closed
