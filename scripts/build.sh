#!/usr/bin/env bash

if [ -d "venv" ]; then
    source ./venv/bin/activate
else
    python3 -m venv venv
    source ./venv/bin/activate
fi

python3 -m pip install build
pip install -r ./requirements.txt
pip install -e .