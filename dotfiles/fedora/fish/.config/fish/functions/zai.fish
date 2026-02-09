function zai --description "Run AI CLI tools with Z.AI GLM Models"
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

    # Execute with Z.AI environment variables
    ANTHROPIC_DEFAULT_OPUS_MODEL=GLM-4.7 \
    ANTHROPIC_DEFAULT_SONNET_MODEL=GLM-4.7 \
    ANTHROPIC_DEFAULT_HAIKU_MODEL=GLM-4.5-Air \
    CLAUDE_CODE_SUBAGENT_MODEL=GLM-4.7 \
    ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic \
    ANTHROPIC_AUTH_TOKEN="$ZAI_API_KEY" \
    CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1 \
    command $cmd $args
end
