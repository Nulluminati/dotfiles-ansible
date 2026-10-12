#!/bin/bash
#
# Claude Code Status Line
# Displays: model, context window %, tokens, git info
#

# Prevent git from taking optional locks that refresh the index.
# This script runs frequently and should never write to the repo.
export GIT_OPTIONAL_LOCKS=0

# Read JSON input from stdin
input=$(cat)

# Debug: Log received JSON to file, uncomment when needed
# echo "$(date '+%Y-%m-%d %H:%M:%S') - PID: $$" >> ~/.claude/statusline-debug.log
# echo "$input" | jq '.' >> ~/.claude/statusline-debug.log 2>&1
# echo "---" >> ~/.claude/statusline-debug.log

# Determine provider from WRAPBOOK_LLM_GATEWAY_ID (set by claude-gateway
# regardless of which backend it selects) or, failing that, ANTHROPIC_BASE_URL
get_provider() {
    if [[ -n "${WRAPBOOK_LLM_GATEWAY_ID:-}" ]]; then
        echo "Wrapbook AI Gateway"
        return
    fi
    case "${ANTHROPIC_BASE_URL:-}" in
        "") echo "Anthropic" ;;
        "https://bifrost.takeone.works"*) echo "Wrapbook AI Gateway" ;;
        "https://api.z.ai/api/anthropic") echo "Z.ai" ;;
        "https://api.synthetic.new/anthropic") echo "Synthetic" ;;
        "https://api.fireworks.ai/inference"*) echo "Fireworks" ;;
        *) echo "Unknown Provider" ;;
    esac
}

# ANSI color codes - use tput if available, otherwise ANSI escapes
if command -v tput >/dev/null 2>&1 && [ -n "$TERM" ] && [ "$TERM" != "dumb" ]; then
    reset() { tput sgr0; }
    bold() { tput bold; }
    dim() { tput dim 2>/dev/null || true; }
    fg_black() { tput setaf 0; }
    fg_red() { tput setaf 1; }
    fg_green() { tput setaf 2; }
    fg_yellow() { tput setaf 3; }
    fg_blue() { tput setaf 4; }
    fg_magenta() { tput setaf 5; }
    fg_cyan() { tput setaf 6; }
    fg_white() { tput setaf 7; }
else
    reset() { printf '\033[0m'; }
    bold() { printf '\033[1m'; }
    dim() { printf '\033[2m'; }
    fg_black() { printf '\033[30m'; }
    fg_red() { printf '\033[31m'; }
    fg_green() { printf '\033[32m'; }
    fg_yellow() { printf '\033[33m'; }
    fg_blue() { printf '\033[34m'; }
    fg_magenta() { printf '\033[35m'; }
    fg_cyan() { printf '\033[36m'; }
    fg_white() { printf '\033[37m'; }
fi

# Separator character
SEP=" $(dim)|$(reset) "

# Extract values from JSON using jq
MODEL_ID=$(echo "$input" | jq -r '.model.id // "?"')
CONTEXT_PERCENT=$(echo "$input" | jq -r '.context_window.used_percentage // 0')
TOTAL_INPUT=$(echo "$input" | jq -r '.context_window.total_input_tokens // 0')
TOTAL_OUTPUT=$(echo "$input" | jq -r '.context_window.total_output_tokens // 0')
CACHE_CREATE=$(echo "$input" | jq -r '.context_window.current_usage.cache_creation_input_tokens // 0')
CACHE_READ=$(echo "$input" | jq -r '.context_window.current_usage.cache_read_input_tokens // 0')

# Subscription rate limits (claude.ai Pro/Max only, absent until first API response)
RL_5H=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty')
RL_5H_RESET=$(echo "$input" | jq -r '.rate_limits.five_hour.resets_at // empty')
RL_7D=$(echo "$input" | jq -r '.rate_limits.seven_day.used_percentage // empty')

# Session display values for the herdr sidebar
SESSION_NAME=$(echo "$input" | jq -r '.session_name // empty')
COST_USD=$(echo "$input" | jq -r '.cost.total_cost_usd // 0')

# Get current directory from workspace
CWD=$(echo "$input" | jq -r '.workspace.current_dir // .cwd // "."')

# Calculate context color based on percentage
context_color() {
    local pct=$1
    if (( $(echo "$pct >= 90" | bc -l 2>/dev/null || echo "0") )); then
        fg_red
    elif (( $(echo "$pct >= 70" | bc -l 2>/dev/null || echo "0") )); then
        fg_yellow
    else
        fg_green
    fi
}

# Format large numbers with k/m suffixes
fmt_num() {
    local num=$1
    if (( num >= 1000000 )); then
        echo "$(echo "scale=1; $num/1000000" | bc 2>/dev/null || echo "$((num/1000000))")m"
    elif (( num >= 1000 )); then
        echo "$(echo "scale=1; $num/1000" | bc 2>/dev/null || echo "$((num/1000))")k"
    else
        echo "$num"
    fi
}

# Get token breakdown using totals for I/O and current_usage for cache
get_token_breakdown() {
    local total=$((TOTAL_INPUT + TOTAL_OUTPUT + CACHE_CREATE + CACHE_READ))

    # Colored labels with formatted values
    echo "$(fg_cyan)I:$(reset)$(fmt_num $TOTAL_INPUT) $(fg_green)O:$(reset)$(fmt_num $TOTAL_OUTPUT) $(fg_yellow)W:$(reset)$(fmt_num $CACHE_CREATE) $(fg_magenta)R:$(reset)$(fmt_num $CACHE_READ) $(fg_white)T:$(reset)$(fmt_num $total)"
}

# Format seconds until a reset as XhYm or Ym; prints nothing once passed
fmt_countdown() {
    local seconds=$(( $1 - $(date +%s) ))
    (( seconds <= 0 )) && return
    local hours=$(( seconds / 3600 ))
    local minutes=$(( seconds % 3600 / 60 ))
    if (( hours > 0 )); then
        echo "${hours}h${minutes}m"
    else
        echo "${minutes}m"
    fi
}

# One rate limit window: "<label>: N% left", colored by percent used
rate_limit_window() {
    local label=$1
    local used=$2
    local reset=$3
    local left=$(printf '%.0f' "$(echo "100 - $used" | bc -l)")
    (( left < 0 )) && left=0

    echo -n "$(fg_white)${label}:$(reset) $(context_color "$used")${left}% left$(reset)"
    if [[ -n "$reset" ]]; then
        local countdown=$(fmt_countdown "$reset")
        [[ -n "$countdown" ]] && echo -n " $(dim)(${countdown})$(reset)"
    fi
}

# Remaining subscription usage for the 5-hour and 7-day windows
rate_limit_info() {
    local parts=()
    [[ -n "$RL_5H" ]] && parts+=("$(rate_limit_window 5h "$RL_5H" "$RL_5H_RESET")")
    [[ -n "$RL_7D" ]] && parts+=("$(rate_limit_window 7d "$RL_7D")")

    local IFS=' '
    echo -n "${parts[*]}"
}

# Git information gathering
git_info() {
    local dir="$CWD"
    local git_dir

    # Check if in a git repo
    git_dir=$(cd "$dir" 2>/dev/null && git rev-parse --git-dir 2>/dev/null)
    [[ -z "$git_dir" ]] && return

    # Get repo name (root directory name)
    local repo_root=$(cd "$dir" 2>/dev/null && git rev-parse --show-toplevel 2>/dev/null)
    local repo_name=$(basename "$repo_root" 2>/dev/null)

    # Get current branch
    local branch=$(cd "$dir" 2>/dev/null && git branch --show-current 2>/dev/null)
    [[ -z "$branch" ]] && branch=$(cd "$dir" 2>/dev/null && git describe --tags --exact-match 2>/dev/null)
    [[ -z "$branch" ]] && branch=$(cd "$dir" 2>/dev/null && git rev-parse --short HEAD 2>/dev/null)

    # Get git status counts
    local staged=0
    local unstaged=0
    local untracked=0

    while IFS= read -r line; do
        local x=${line:0:1}
        local y=${line:1:1}

        # Untracked files - check first and skip other checks
        if [[ "$x" == "?" ]]; then
            ((untracked++))
            continue
        fi

        # Staged changes (index has something other than space)
        [[ "$x" != " " ]] && ((staged++))

        # Unstaged changes (work tree has something other than space)
        [[ "$y" != " " ]] && ((unstaged++))
    done < <(cd "$dir" 2>/dev/null && git status --porcelain 2>/dev/null)

    # Get diff stats (lines added/removed)
    local lines_added=0
    local lines_removed=0
    local diff_stat=$(cd "$dir" 2>/dev/null && git diff --shortstat 2>/dev/null)
    if [[ -n "$diff_stat" ]]; then
        # Parse "1 file changed, 10 insertions(+), 5 deletions(-)" format
        lines_added=$(echo "$diff_stat" | grep -oP '\d+(?= insertion)' || echo 0)
        lines_removed=$(echo "$diff_stat" | grep -oP '\d+(?= deletion)' || echo 0)
    fi

    # Build status string
    local status_parts=()
    (( staged > 0 )) && status_parts+=("+${staged}")
    (( unstaged > 0 )) && status_parts+=("~${unstaged}")
    (( untracked > 0 )) && status_parts+=("?${untracked}")

    # Add line changes if any
    local line_changes=""
    if (( lines_added > 0 )); then
        line_changes+="$(fg_green)+${lines_added}$(reset)"
        (( lines_removed > 0 )) && line_changes+=" "
    fi
    (( lines_removed > 0 )) && line_changes+="$(fg_red)-${lines_removed}$(reset)"

    local IFS=' '
    local status_str="${status_parts[*]}"

    # Output: repo@branch [status] [+lines -lines]
    echo -n "$(fg_blue)${repo_name}$(reset)"
    echo -n "$(fg_cyan)@$(reset)"
    echo -n "$(fg_magenta)${branch}$(reset)"
    [[ -n "$status_str" ]] && echo -n " [$(fg_yellow)${status_str}$(reset)]"
    [[ -n "$line_changes" ]] && echo -n " [${line_changes}]"
}

# Build status line components
provider_section="$(bold)$(fg_yellow)$(get_provider)$(reset)"
model_section="$(bold)$(fg_cyan)${MODEL_ID}$(reset)"
context_section="$(fg_white)Ctx:$(reset) $(context_color "$CONTEXT_PERCENT")${CONTEXT_PERCENT}%$(reset)"
rate_limit_section=$(rate_limit_info)
token_section="$(get_token_breakdown)"
git_section=$(git_info)

# Assemble status line with separators
status_line=""
status_line+="${provider_section}"
status_line+="${SEP}${model_section}"
status_line+="${SEP}${context_section}"
[[ -n "$rate_limit_section" ]] && status_line+="${SEP}${rate_limit_section}"
status_line+="${SEP}${token_section}"
[[ -n "$git_section" ]] && status_line+="${SEP}${git_section}"

printf '%s' "$status_line"

# Publish session name, context and cost as herdr sidebar tokens
# ($claude_session_name, $claude_context, $claude_cost). Tokens without a
# TTL persist until replaced or the pane closes.
report_herdr_metadata() {
    [[ "${HERDR_ENV:-}" == "1" && -n "${HERDR_PANE_ID:-}" ]] || return 0

    local args=(
        pane report-metadata "$HERDR_PANE_ID"
        --source user:claude-statusline
        --seq "$(date +%s%N)"
        --token "claude_context=ctx ${CONTEXT_PERCENT}%"
        --token "claude_cost=\$$(printf '%.3f' "$COST_USD")"
    )
    if [[ -n "$SESSION_NAME" ]]; then
        args+=(--token "claude_session_name=${SESSION_NAME}")
    else
        args+=(--clear-token claude_session_name)
    fi

    "${HERDR_BIN_PATH:-herdr}" "${args[@]}" >/dev/null 2>&1 || true
}

# Mirror the session name onto the herdr pane label. Rename only when the
# name changes, so a label set by hand in herdr survives until the next
# session name. An unnamed session leaves the existing label alone.
rename_herdr_pane() {
    [[ "${HERDR_ENV:-}" == "1" && -n "${HERDR_PANE_ID:-}" && -n "$SESSION_NAME" ]] || return 0

    local cache="${XDG_RUNTIME_DIR:-/tmp}/claude-herdr-pane-name-${HERDR_PANE_ID//[^A-Za-z0-9]/_}"
    [[ "$(cat "$cache" 2>/dev/null)" == "$SESSION_NAME" ]] && return 0

    "${HERDR_BIN_PATH:-herdr}" pane rename "$HERDR_PANE_ID" "$SESSION_NAME" >/dev/null 2>&1 \
        && printf '%s' "$SESSION_NAME" > "$cache"
    return 0
}

report_herdr_metadata
rename_herdr_pane
