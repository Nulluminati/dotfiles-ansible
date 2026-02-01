#!/usr/bin/env fish

# Terminate already running bar instances
killall -q polybar

# Wait until the processes have been shut down
while pgrep -x polybar >/dev/null
    sleep 1
end

for m in (polybar --list-monitors | cut -d":" -f1)
    set -x MONITOR $m
    polybar --reload top -r &
end
