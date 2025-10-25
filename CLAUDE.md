# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python library (`connbox`) that provides an HTTP API to interact with Connection Box (connBox/cBox) devices installed on pellet stoves with Fumis Controllers (brands: Palazzetti, Jotul, TurboFonte, Godin, etc.).

## Python Package Management with uv

Use uv exclusively for Python package management in this project.

### Package Management Commands

- All Python dependencies **must be installed, synchronized, and locked** using uv
- Never use pip, pip-tools, poetry, or conda directly for dependency management

Use these commands:

- Install dependencies: `uv add <package>`
- Remove dependencies: `uv remove <package>`
- Sync dependencies: `uv sync`

### Running Python Code

- Run a Python script with `uv run <script-name>.py`
- Run Python tools like Pytest with `uv run pytest` or `uv run ruff`
- Launch a Python repl with `uv run python`

### Managing Scripts with PEP 723 Inline Metadata

- Run a Python script with inline metadata (dependencies defined at the top of the file) with: `uv run script.py`
- You can add or remove dependencies manually from the `dependencies =` section at the top of the script, or
- Or using uv CLI:
  - `uv add package-name --script script.py`
  - `uv remove package-name --script script.py`

## Development Commands

### Testing

Run all tests:
```bash
uv run pytest
```

Run a single test file:
```bash
uv run pytest tests/connbox_test.py
```

Run a specific test function:
```bash
uv run pytest tests/connbox_test.py::test_cbox_should_fetch_infos
```

Run tests with coverage:
```bash
uv run coverage run -m pytest
uv run coverage report
```

### Linting and Formatting

Format and lint code with Ruff:
```bash
uv run ruff check
uv run ruff format
```

Line length is configured to 120 characters in `pyproject.toml`.

### Local Development Workbench

Use `workbench_for_local_dev.py` to interact with a real connBox device on your LAN. This script demonstrates the typical usage patterns of the library.

## Code Architecture

### Core Module: `src/connbox/connbox.py`

The main `Cbox` class provides async context manager support for connecting to and controlling a connBox device:

**Key Classes:**
- `Cbox`: Main API class that uses aiohttp's ClientSession for HTTP communication
  - Uses async context manager pattern (`async with Cbox.connected_to(host)`)
  - All API methods are async and raise exceptions on failure
  - Endpoint: `/cgi-bin/sendmsg.lua` with query parameter `cmd`

- `CboxInfo`: Dataclass representing the state of the device (temperatures, setpoints, status, firmware info)
  - Includes factory method `from_dict()` to parse API responses
  - Custom `__repr__()` returns JSON representation

- `StoveStatus`: Enum of device operational states (OFF, BURNING, HEATUP, various alarms)
- `FanStatus`: Enum of fan speed settings (OFF, SPEED_1-5, HIGH, AUTO)

**API Methods:**
- `fetch_info()`: Gets complete device state via `GET ALLS` command
- `power_on()` / `power_off()`: Control device power via `CMD on/off`
- `change_temperature_setpoint(temp)`: Set target temperature (12-50°C) via `SET SETP`
- `change_power_setpoint(power)`: Set power level (1-5) via `SET POWR`
- `change_fan_setpoint(fan_status)`: Set fan speed via `SET RFAN`

### Test Infrastructure: `tests/connbox_simulator.py`

`CboxSimulator` provides a mock aiohttp server that simulates connBox HTTP responses:
- Used in pytest fixtures to test without real hardware
- Maintains internal state (`CboxInfo`) that responds to commands
- Parses regex patterns to match real connBox command format
- Returns JSON responses matching real device structure

### Testing Strategy

Tests use pytest-asyncio and pytest-aiohttp:
- `simulator` fixture provides a CboxSimulator instance
- `cbox` fixture provides a Cbox instance connected to the simulator
- Tests verify both successful operations and state changes
- Example: `test_cbox_should_power_on` verifies status changes from OFF to BURNING

### Async/IO Pattern

All I/O operations are async using:
- Python's asyncio library for async/await syntax
- aiohttp for HTTP client operations
- pytest-asyncio for async test support (configured with `asyncio_mode = "auto"` in pyproject.toml)

## Python Version

This project requires Python 3.13 or higher. The CI pipeline tests against Python 3.13.

## Project Structure

```
src/connbox/          # Main package source
  connbox.py         # Core API implementation
  __init__.py        # Package initialization
tests/               # Test suite
  connbox_test.py    # Main test cases
  connbox_simulator.py # Mock server for testing
doc/                 # Documentation
  cboxProtcol.md     # Protocol documentation for curl interactions
workbench_for_local_dev.py  # Development script for manual testing
```

## CI/CD

GitHub Actions workflow (`.github/workflows/ci.yml`) runs on push to main:
1. Runs pytest test suite
2. On tagged releases (`v*`), automatically publishes to PyPI using trusted publishing

## Protocol Documentation

For details on the connBox HTTP protocol and curl examples, see `doc/cboxProtcol.md`.
