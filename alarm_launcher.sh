#!/bin/bash
# Get user context
USER=$(whoami)
export HOME=/home/$USER

# Generate Xauth if missing
if [ ! -f ~/.Xauthority ]; then
    touch ~/.Xauthority
    xauth add :0 . $(mcookie) >/dev/null 2>&1
fi

# Use current display or default to :0
ACTIVE_DISPLAY=$(w -hs | awk '{print $3}' | grep ':[0-9]' | head -1)
export DISPLAY=${ACTIVE_DISPLAY:-:0}

# Create secure temp Xauth file
XFILE="/tmp/alarm_xauth_${USER}_${DISPLAY#:}"
cp -f ~/.Xauthority "$XFILE"
chmod 600 "$XFILE"
export XAUTHORITY="$XFILE"

# Audio setup
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$(id -u)/bus
export PULSE_SERVER=unix:/run/user/$(id -u)/pulse/native

# Debug logging
exec >> "/tmp/alarm_debug_$(date +%F).log" 2>&1
echo "=== Alarm triggered $(date) ==="
echo "Using DISPLAY: $DISPLAY"
echo "Xauth contents:"
xauth -f "$XFILE" list

# Run alarm
cd "$(dirname "$0")"
/usr/bin/python3 cronalarmv3.py --trigger "$1" "$2"

# Cleanup
rm -f "$XFILE"