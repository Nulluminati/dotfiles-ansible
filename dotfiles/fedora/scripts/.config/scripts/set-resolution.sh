#!/bin/bash
# Set screen resolution for Intel iGPU passthrough with EDID
# Waits for display to be ready, then sets 2560x1440

sleep 2

# Check if HDMI-1 is connected
if xrandr | grep "HDMI-1 connected" > /dev/null 2>&1; then
    # Add 2560x1440 mode if it doesn't exist
    xrandr --newmode "2560x1440_60" 241.50 2560 2608 2640 2720 1440 1443 1448 1481 +hsync +vsync 2>/dev/null
    xrandr --addmode HDMI-1 2560x1440_60 2>/dev/null

    # Set the resolution
    xrandr --output HDMI-1 --mode 2560x1440_60 --primary
fi
