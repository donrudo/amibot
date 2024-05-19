#!/usr/bin/env bash

source venv/bin/activate

if [ -n "$1" ]; then
  python3 amibot -c configs/amibot.conf
else
  python3 amibot -c $1
fi