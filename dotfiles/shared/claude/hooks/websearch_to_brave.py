#!/usr/bin/env python3
"""
PreToolUse hook: intercept WebSearch → suggest using brave search instead
"""
import json
import sys

try:
    data = json.load(sys.stdin)
    tool_input = data["tool_input"]
    query = tool_input["query"]
except (KeyError, json.JSONDecodeError) as err:
    print(f"hook-error: {err}", file=sys.stderr)
    sys.exit(1)

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": f"Please use mcp__brave-search__brave_web_search with query: '{query}'"
    }
}, separators=(',', ':')))
sys.exit(0)