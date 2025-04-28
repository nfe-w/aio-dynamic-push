#!/bin/sh
set -e

if [ ! -f /mnt/config.yml ]; then
  echo 'Error: /mnt/config.yml file not found. Please mount the /mnt/config.yml file and try again.'
  exit 1
fi

cp -f /mnt/config.yml /app/config.yml
exec /app/.venv/bin/python -u main.py
