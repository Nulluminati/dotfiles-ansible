function firepass --description "Run AI CLI tools with Fireworks AI Kimi Models"
    # Default to claude if no command specified
    set -l cmd "claude"
    set -l args $argv

    if test (count $argv) -gt 0
        set cmd $argv[1]
        set args $argv[2..-1]
    end

    # Validate command exists
    if not type -q $cmd
        echo "Error: Command '$cmd' not found." >&2
        return 1
    end

    # Fireworks AI model for Kimi
    set -l model accounts/fireworks/routers/kimi-k2p5-turbo

    # Execute with Fireworks AI environment variables
    ANTHROPIC_DEFAULT_OPUS_MODEL=$model \
    ANTHROPIC_DEFAULT_SONNET_MODEL=$model \
    ANTHROPIC_DEFAULT_HAIKU_MODEL=$model \
    CLAUDE_CODE_SUBAGENT_MODEL=$model \
    ANTHROPIC_BASE_URL=https://api.fireworks.ai/inference \
    ANTHROPIC_AUTH_TOKEN="$FIREWORKS_API_KEY" \
    CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1 \
    command $cmd $args
end
