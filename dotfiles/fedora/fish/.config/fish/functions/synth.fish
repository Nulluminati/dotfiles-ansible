function synth --description "Run AI CLI tools with Synthetic.new Models"
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

    # Execute with Synthetic.new environment variables
    ANTHROPIC_BASE_URL=https://api.synthetic.new/anthropic \
    ANTHROPIC_AUTH_TOKEN="$SYNTHETIC_API_KEY" \
    ANTHROPIC_DEFAULT_OPUS_MODEL=hf:nvidia/Kimi-K2.5-NVFP4 \
    ANTHROPIC_DEFAULT_SONNET_MODEL=hf:nvidia/Kimi-K2.5-NVFP4 \
    ANTHROPIC_DEFAULT_HAIKU_MODEL=hf:MiniMaxAI/MiniMax-M2.1 \
    CLAUDE_CODE_SUBAGENT_MODEL=hf:nvidia/Kimi-K2.5-NVFP4 \
    CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1 \
    command $cmd $args
end
