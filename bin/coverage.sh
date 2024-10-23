#!/bin/sh

cd ..
poetry run coverage run --source=cbox -m pytest
poetry run coverage html