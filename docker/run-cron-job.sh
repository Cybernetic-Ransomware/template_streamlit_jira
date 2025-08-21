#!/bin/bash

export PATH="/src/.venv/bin:$PATH"

cd /src

exec python /src/core/db/cron.py