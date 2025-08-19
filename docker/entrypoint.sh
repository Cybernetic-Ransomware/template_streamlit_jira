#!/bin/bash

echo "Starting crond in foreground..."
crond -f -L /log/snapshooter.log
