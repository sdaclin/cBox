import asyncio
import logging
import sys

from cbox.connbox import Cbox, CboxInfo
from cbox.model import FanStatus, StoveStatus


async def main():
    # Configure the logger to be verbose with the cbox module
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    logging.getLogger('cbox.connbox').setLevel(logging.DEBUG)

    # Define your cbox host (could be an ip address like 192.168.0.14)
    host: str = "connbox"

    # Use your cbox
    async with Cbox.connected_to(host) as cbox:
        # Fetch current cbox info
        print(await cbox.fetch_info())

        # Change cbox settings
        await cbox.change_status(Cbox.Status.OFF)
        await cbox.change_fan_setpoint(FanStatus.AUTO)
        await cbox.change_temperature_setpoint(19)
        await cbox.change_power_setpoint(4)

        # Fetch changed cbox info
        print(await cbox.fetch_info())

asyncio.run(main())
