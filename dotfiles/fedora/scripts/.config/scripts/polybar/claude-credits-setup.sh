#!/bin/bash
# Rofi prompt for Claude Organization ID
# Called when user clicks the polybar module

# Ensure DISPLAY is set for rofi
export DISPLAY=:0

CONFIG_DIR="$HOME/.config/anthropic"
mkdir -p "$CONFIG_DIR"
chmod 700 "$CONFIG_DIR"

# Get Organization ID via rofi
# Using theme-str to ensure prompt/message are visible (config.rasi doesn't include them in inputbar)
ORG_ID=$(rofi -dmenu \
    -p " Org ID" \
    -mesg "Paste your Anthropic Organization ID from platform.claude.com/settings/organization" \
    -theme-str 'mainbox { children: [ message, inputbar ]; }' \
    -theme-str 'message { background-color: @background; text-color: @foreground; padding: 8px; }' \
    -theme-str 'inputbar { children: [ prompt, entry ]; }' \
    -theme-str 'prompt { background-color: @background; text-color: @foreground; padding: 8px; border: 0px 0px 2px 0px; border-color: @border-color; }' \
    -theme-str 'entry { placeholder: "org-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"; }')

# User cancelled
if [ -z "$ORG_ID" ]; then
    exit 0
fi

# Save org ID
echo "$ORG_ID" > "$CONFIG_DIR/org_id"
chmod 600 "$CONFIG_DIR/org_id"

# Notify user
notify-send "Claude Credits" "Organization ID saved. Ensure you're logged into platform.claude.com in Firefox."
