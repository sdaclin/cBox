from datetime import datetime, date

from enum import Enum

from dataclasses import dataclass

import json


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

    status: StoveStatus = StoveStatus.OFF

    fanSetpoint: FanStatus = FanStatus.OFF
    powerSetpoint: int = 1
    temperatureSetpoint: int = 19

    t1: int = 0
    t2: int = 0
    t3: int = 0
    t4: int = 0
    t5: int = 0

    firmwareVersion: int = 0
    firmwareDate: date = date.today()

    def __repr__(self) -> str:
        return json.dumps({
            'timestamp': str(self.timestamp),
            'globalStatus': self.status.name,
            'fanSetpoint': self.fanSetpoint.name,
            'powerSetpoint': self.powerSetpoint,
            'temperatureSetpoint': self.temperatureSetpoint,
            'temperature1': self.t1,
            'temperature2': self.t2,
            'temperature3': self.t3,
            'temperature4': self.t4,
            'temperature5': self.t5,
            'firmwareDate': str(self.firmwareDate),
            'firmwareVersion': self.firmwareVersion
        })

    def from_dict(dict: dict) -> 'CboxInfo':
        return CboxInfo(timestamp=datetime.fromtimestamp(dict['INFO']['TS']),
                        status=StoveStatus(dict['DATA']['STATUS']),
                        fanSetpoint=FanStatus(dict['DATA']['F2L']),
                        powerSetpoint=dict['DATA']['PWR'],
                        temperatureSetpoint=dict['DATA']['SETP'],
                        t1=dict['DATA']['T1'],
                        t2=dict['DATA']['T2'],
                        t3=dict['DATA']['T3'],
                        t4=dict['DATA']['T4'],
                        t5=dict['DATA']['T5'],
                        firmwareVersion=int(dict['DATA']['VER']),
                        firmwareDate=date.fromisoformat(dict['DATA']['FWDATE'])
                        )
