#!/bin/bash
# Rofi prompt for the OpenCode Go workspace ID.
# Called when the user right-clicks the polybar module.
#
# The workspace ID looks like "wrk_01ABCDEF0123456789ABCDEFG" and appears in the
# dashboard URL: https://opencode.ai/workspace/<workspaceId>/go
#
# The auth session cookie is read from the browser automatically, so make sure
# you are signed in to opencode.ai in Firefox.

# Ensure DISPLAY is set for rofi
export DISPLAY=:0

CONFIG_DIR="$HOME/.config/opencode"
mkdir -p "$CONFIG_DIR"
chmod 700 "$CONFIG_DIR"

# Get Workspace ID via rofi
WORKSPACE_ID=$(rofi -dmenu \
    -p " Workspace" \
    -mesg "Paste your OpenCode workspace ID (e.g. wrk_01ABC...) from opencode.ai/dashboard URL" \
    -theme-str 'mainbox { children: [ message, inputbar ]; }' \
    -theme-str 'message { background-color: @background; text-color: @foreground; padding: 8px; }' \
    -theme-str 'inputbar { children: [ prompt, entry ]; }' \
    -theme-str 'prompt { background-color: @background; text-color: @foreground; padding: 8px; border: 0px 0px 2px 0px; border-color: @border-color; }' \
    -theme-str 'entry { placeholder: "wrk_0123456789ABCDEF"; }')

# User cancelled
if [ -z "$WORKSPACE_ID" ]; then
    exit 0
fi

# Save workspace ID
echo "$WORKSPACE_ID" > "$CONFIG_DIR/workspace_id"
chmod 600 "$CONFIG_DIR/workspace_id"

# Notify user
notify-send "OpenCode Go" "Workspace ID saved. Ensure you're signed into opencode.ai in Firefox."
