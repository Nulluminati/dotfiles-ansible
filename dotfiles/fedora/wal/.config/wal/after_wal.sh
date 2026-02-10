#!/usr/bin/env bash

# Source the colors from wal
source "${HOME}/.cache/wal/colors.sh"

ln -sf "${HOME}/.cache/wal/dunstrc" "${HOME}/.config/dunst/dunstrc"

# Restart dunst with the new color scheme
pkill dunst
dunst &

# Generate Sublime Text color scheme from pywal colors
if command -v python3 &>/dev/null; then
    python3 "${HOME}/.config/scripts/pywal-sublime.py"
fi
