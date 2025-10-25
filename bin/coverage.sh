#!/bin/sh

cd ..
uv run coverage run --source=connbox -m pytest
uv run coverage html