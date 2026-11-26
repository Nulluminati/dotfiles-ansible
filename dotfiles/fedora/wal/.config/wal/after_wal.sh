#!/usr/bin/env bash

# Source the colors from wal
source "${HOME}/.cache/wal/colors.sh"

ln -sf "${HOME}/.cache/wal/dunstrc" "${HOME}/.config/dunst/dunstrc"

# Restart dunst with the new color scheme
pkill dunst
dunst &

# Ghostty runs as a single-instance server that reads ~/.cache/wal/ghostty.conf
# only at startup. SIGUSR2 tells it to reload config so new windows use the
# current colors instead of the colors from when the server started.
pkill -USR2 -x ghostty

# Generate Sublime Text color scheme from pywal colors
if command -v python3 &>/dev/null; then
    python3 "${HOME}/.config/scripts/pywal-sublime.py"
fi
