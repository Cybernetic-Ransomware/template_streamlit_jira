#!/bin/bash
SHELL=/bin/bash

echo "Saving environment variables..."
printenv | grep -v "no_proxy" > /etc/environment

echo "Starting cron in foreground..."
cron -f -L 1