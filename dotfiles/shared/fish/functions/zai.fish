function zai --description "Run AI CLI tools with Z.AI GLM Models"
    # Default to pi if no command specified
    set -l cmd "pi"
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

    # Model list depends on the consumer: pi uses lowercase registry IDs,
    # Claude Code uses the Anthropic-style PascalCase IDs.
    # Declare at function scope so it survives the if-block.
    set -l models
    if test "$cmd" = "pi"
        # Query pi for the current zai model list so this stays in sync with
        # pi releases without needing to update this file.
        set models (pi --list-models | awk 'NR > 1 && $1 == "zai" {print $2}')
        if test -z "$models"
            echo "Error: No zai models found via 'pi --list-models'" >&2
            return 1
        end
    else
        set models GLM-5.1 GLM-5 GLM-5-Turbo GLM-4.7
    end

    set -l selected_model (printf '%s\n' $models | fzf --prompt='Select model: ' --height=~50%)

    if test $status -ne 0 -o -z "$selected_model"
        return 1
    end

    if test "$cmd" = "pi"
        command pi --provider zai --model $selected_model $args
    else
        ANTHROPIC_DEFAULT_OPUS_MODEL=$selected_model \
        ANTHROPIC_DEFAULT_SONNET_MODEL=$selected_model \
        ANTHROPIC_DEFAULT_HAIKU_MODEL=GLM-4.5-Air \
        CLAUDE_CODE_SUBAGENT_MODEL=$selected_model \
        ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic \
        ANTHROPIC_AUTH_TOKEN="$ZAI_API_KEY" \
        CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1 \
        command $cmd $args
    end
end
