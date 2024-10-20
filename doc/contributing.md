# Contributing

## Requesting support for other stoves

If your stove behaves differently than mine (Jotul 1033) then I invite you to interact with it with `curl` and send me sample of interaction so that I can integrate them through a config file or a generic implementation.

* See [cboxProtcol.md](cboxProtcol.md) to find out how to use `curl`

## Proposing PR

They are more than welcome :love:

## Good to know

Here are some interesting readings around this repo : 

* [Poetry](https://python-poetry.org/) for packaging and dependency management
* [Python - asyncio](https://realpython.com/async-io-python/) for async support when doing i/o like `http` requests
* [Python - aiohttp](https://docs.aiohttp.org/en/stable/) the lib used for `http` support
* [Python - pytest-asyncio](https://pytest-asyncio.readthedocs.io/en/latest/index.html) to handle `pytests` in an async way
