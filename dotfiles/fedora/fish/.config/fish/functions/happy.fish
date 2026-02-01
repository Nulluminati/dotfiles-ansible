function happy --description "Happy Coder CLI with provider selection"
    set -l provider ""
    set -l provider_args ""

    # Parse arguments for -p/--provider flag
    for i in (seq (count $argv))
        switch $argv[$i]
            case -p --provider
                if test $i -lt (count $argv)
                    set provider $argv[(math $i + 1)]
                    # Remove provider and its value from argv
                    set -e argv[$i..(math $i + 1)]
                    break
                end
        end
    end

    # Set provider-specific environment variables
    switch $provider
        case zai
            set provider_args \
                --claude-env "ANTHROPIC_DEFAULT_OPUS_MODEL=GLM-4.7" \
                --claude-env "ANTHROPIC_DEFAULT_SONNET_MODEL=GLM-4.7" \
                --claude-env "ANTHROPIC_DEFAULT_HAIKU_MODEL=GLM-4.5-Air" \
                --claude-env "CLAUDE_CODE_SUBAGENT_MODEL=GLM-4.7" \
                --claude-env "ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic" \
                --claude-env "ANTHROPIC_AUTH_TOKEN=$ZAI_API_KEY" \
                --claude-env "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1"

        case synth synthetic
            set provider_args \
                --claude-env "ANTHROPIC_BASE_URL=https://api.synthetic.new/anthropic" \
                --claude-env "ANTHROPIC_AUTH_TOKEN=$SYNTHETIC_NEW_API_KEY" \
                --claude-env "ANTHROPIC_DEFAULT_OPUS_MODEL=hf:moonshotai/Kimi-K2.5" \
                --claude-env "ANTHROPIC_DEFAULT_SONNET_MODEL=hf:moonshotai/Kimi-K2.5" \
                --claude-env "ANTHROPIC_DEFAULT_HAIKU_MODEL=hf:moonshotai/Kimi-K2.5" \
                --claude-env "CLAUDE_CODE_SUBAGENT_MODEL=hf:moonshotai/Kimi-K2.5" \
                --claude-env "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1"

        case claude ""
            # Default: no extra env vars, use standard Claude
            set provider_args ""

        case '*'
            echo "Error: Unknown provider '$provider'" >&2
            echo "Valid providers: zai, synth, claude" >&2
            return 1
    end

    command happy $provider_args $argv
end
