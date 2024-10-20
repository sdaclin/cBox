# Cbox protocol

Here is the observed protocol as for a [Jotul 1033 Stove](https://www.jotul.fr/produits/granules-de-bois/poele-granules-design-et-etanche/jotul-pf-1033).
All this project is based on it, feel free to contribute with other references or brands.

## GET ALLS (get current stove status)

```sh
curl -d cmd='GET ALLS' "http://$host/cgi-bin/sendmsg.lua"
```

```Json
{
    "INFO": {
        "RSP": "OK",
        "CMD": "GET ALLS",
        "TS": 1728725454
    },
    "SUCCESS": true,
    "DATA": {
        "T2": 0,
        "F2LF": 2,
        "PQT": 42,
        "PWR": 3,
        "CHRSTATUS": 0,
        "SECO": 1.2,
        "FDR": 2,
        "F2V": 120,
        "MOD": 646,
        "DPT": 0,
        "APLWDAY": 6,
        "MAC": "FF:FF:FF:FF:FF:FF",
        "SETP": 23,
        "APLTS": "2024-10-12 11:31:48",
        "BECO": 0,
        "STATUS": 6,
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
        "F2L": 7,
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
}
```

:bulb: MAC address has been anonymized

## CMD (power on/off)

```sh
curl -d cmd='CMD on' "http://$host/cgi-bin/sendmsg.lua"
curl -d cmd='CMD off' "http://$host/cgi-bin/sendmsg.lua"
```

## Set temperature setpoint

```sh
curl -d cmd='SET SETP 19' "http://$host/cgi-bin/sendmsg.lua"
```

## Set power setpoint

```sh
curl -d cmd='SET POWR 1' "http://$host/cgi-bin/sendmsg.lua"
```

:bulb: 1 < POWR < 5

## Set fan speed setpoint

```sh
curl -d cmd='SET RFAN 0' "http://$host/cgi-bin/sendmsg.lua"
```

| Value | Meaning |
|-------|---------|
| 0     | OFF     |
| 1     | Speed 1 |
| 2     | Speed 2 |
| 3     | Speed 3 |
| 4     | Speed 4 |
| 5     | Speed 5 |
| 6     | HIGH    |
| 7     | Auto    |

:bulb: A Jotul 1033 stove will accept 0 but automagically transform it to 1 (fan can't be stopped)
