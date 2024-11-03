from aiohttp import web
from enum import Enum
import re
from cbox.connbox import CboxInfo, StoveStatus, FanStatus


class CboxSimulator:
    CMD_PATTERN = re.compile(r'CMD (on|off)')
    SETP_PATTERN = re.compile(r'SET SETP (\d+)')
    POWR_PATTERN = re.compile(r'SET POWR (\d)')
    RFAN_PATTERN = re.compile(r'SET RFAN (\d)')

    cboxInfo: CboxInfo = CboxInfo()

    class Command(Enum):
        CMD = 0,
        SETP = 1,
        POWR = 2,
        RFAN = 4

    def __init__(self) -> None:
        self.app: web.Application = web.Application()
        self.app.add_routes([
            web.get('/cgi-bin/sendmsg.lua', self.__send_msg_endpoint)
        ])

    def app(self) -> web.Application:
        return self.app

    async def __send_msg_endpoint(self, request):
        command = request.query['cmd']
        if command is None:
            return web.Response(status=web.HTTPBadRequest)

        if command == 'GET ALLS':
            return self.__get_alls_response()

        cmd_matcher = CboxSimulator.CMD_PATTERN.fullmatch(command)
        if cmd_matcher:
            return self.__simulate_command_cmd(cmd_matcher.group(1) == 'on')

        setp_matcher = CboxSimulator.SETP_PATTERN.fullmatch(command)
        if setp_matcher:
            return self.__simulate_command_temperature_setpoint(int(setp_matcher.group(1)))

        powr_matcher = CboxSimulator.POWR_PATTERN.fullmatch(command)
        if powr_matcher:
            return self.__simulate_command_power_setpoint(int(powr_matcher.group(1)))

        fan_matcher = CboxSimulator.RFAN_PATTERN.fullmatch(command)
        if fan_matcher:
            return self.__simulate_command_fan_setpoint(int(fan_matcher.group(1)))

        return web.Response(status=web.HTTPBadRequest)

    def __get_alls_response(self) -> web.Response:
        return web.json_response({
            "INFO": {
                "RSP": "OK",
                "CMD": "GET ALLS",
                "TS": 1728725454
            },
            "SUCCESS": True,
            "DATA": {
                "T2": 0,
                "F2LF": 2,
                "PQT": 42,
                "PWR": self.cboxInfo.powerSetpoint,
                "CHRSTATUS": 0,
                "SECO": 1.2,
                "FDR": 2,
                "F2V": 120,
                "MOD": 646,
                "DPT": 0,
                "APLWDAY": 6,
                "MAC": "FF:FF:FF:FF:FF:FF",
                "SETP": self.cboxInfo.temperatureSetpoint,
                "APLTS": "2024-10-12 11:31:48",
                "BECO": 0,
                "STATUS": self.cboxInfo.status.value,
                "T3": 133,
                "T1": 24.8,
                "PUMP": 0,
                "T5": 49,
                "F1RPM": 1130,
                "OUT": 6,
                "F1V": 1130,
                "EFLAGS": 0,
                "LSTATUS": 6,
                "T4": 0,
                "F2L": self.cboxInfo.fanSetpoint.value,
                "CORE": 20,
                "DP": 0,
                "FANLMINMAX": [
                    2,
                    5,
                    0,
                    1,
                    0,
                    1
                ],
                "IN": 7,
                "VER": 48,
                "MBTYPE": 0,
                "FWDATE": "2023-07-26"
            }
        })

    def __simulate_command_cmd(self, switch: bool) -> web.Response:
        self.cboxInfo.status = StoveStatus.BURNING if switch else StoveStatus.OFF
        return web.json_response({"SUCCESS": True})

    def __simulate_command_temperature_setpoint(self, temperature: int) -> web.Response:
        if temperature < 12:
            temperature = 12
        if temperature > 51:
            temperature = 51
        self.cboxInfo.temperatureSetpoint = temperature
        return web.json_response({"SUCCESS": True})

    def __simulate_command_power_setpoint(self, power: int) -> web.Response:
        if not 0 < power < 6:
            return self.__build_error_response('SET POWR')
        self.cboxInfo.powerSetpoint = power
        return web.json_response({"SUCCESS": True})

    def __simulate_command_fan_setpoint(self, value: int) -> web.Response:
        if not 0 <= value <= 7:
            return self.__build_error_response('SET RFAN')
        self.cboxInfo.fanSetpoint = FanStatus(value)
        return web.json_response({"SUCCESS": True})

    def __build_error_response(self, cmd: str) -> web.Response:
        return web.json_response({
            'INFO': {'RSP': 'ERROR', 'CMD': cmd, 'TS': 1729331226},
            'SUCCESS': False,
            'DATA': {'NODATA': True}
        })
