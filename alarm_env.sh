#!/bin/bash
# Save this in your project folder as alarm_env.sh
export DISPLAY=:0
export XAUTHORITY=$(ps -u $(whoami) -o pid= | xargs -I{} cat /proc/{}/environ 2>/dev/null | tr '\0' '\n' | grep '^XAUTHORITY=' | cut -d= -f2)
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$(id -u)/bus
export PULSE_SERVER=unix:/run/user/$(id -u)/pulse/native
export PYTHONPATH=/usr/lib/python3/dist-packages