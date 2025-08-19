#!/bin/bash

export PATH="/src/.venv/bin:$PATH"

cd /src

exec python /src/db/cron.py