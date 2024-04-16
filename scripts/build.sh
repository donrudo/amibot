#!/usr/bin/env bash

if [ -d "venv" ]; then
    source venv/bin/activate
else
    python3 -m venv venv
    source venv/bin/activate
fi

pip install build
python -m build
pip install -r requirements.txt
pip install -e .