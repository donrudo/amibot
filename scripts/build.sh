#!/usr/bin/env bash

pip install build
pip install -r requirements.txt
pip -m build
pip install -e .