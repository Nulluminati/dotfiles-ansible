#!/bin/bash

updates=$(dnf repoquery -q --upgrades | wc -l)

if [ "$updates" -gt 0 ]; then
    echo "󰏔  $updates"
else
    echo "󰏔  0"
fi
