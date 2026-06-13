function synth --description "Run AI CLI tools with Synthetic.new Models"
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

    set -l models
    if test "$cmd" = "pi"
        # Query pi for the current synthetic model list so this stays in sync
        # with pi releases without needing to update this file.
        set models (pi --list-models | awk 'NR > 1 && $1 == "synthetic" {print $2}')
        if test -z "$models"
            echo "Error: No synthetic models found via 'pi --list-models'" >&2
            return 1
        end

        set -l selected_model (printf '%s\n' $models | fzf --prompt='Select model: ' --height=~50%)

        if test $status -ne 0 -o -z "$selected_model"
            return 1
        end

        command pi --provider synthetic --model $selected_model $args
    else
        # Legacy path: fetch live model list from Synthetic's API for Claude Code
        set -l models_json (curl -s https://api.synthetic.new/openai/v1/models)
        if test $status -ne 0
            echo "Error: Failed to fetch models from Synthetic.new API" >&2
            return 1
        end

        set -l model_ids (echo $models_json | jq -r '.data[].id')
        set -l model_names (echo $models_json | jq -r '.data[].name')

        set -l selected_name (printf '%s\n' $model_names | fzf --prompt='Select model: ' --height=~50%)

        if test $status -ne 0 -o -z "$selected_name"
            return 1
        end

        set -l selected_model
        for i in (seq (count $model_names))
            if test "$model_names[$i]" = "$selected_name"
                set selected_model $model_ids[$i]
                break
            end
        end

        ANTHROPIC_BASE_URL=https://api.synthetic.new/anthropic \
        ANTHROPIC_AUTH_TOKEN="$SYNTHETIC_API_KEY" \
        ANTHROPIC_DEFAULT_OPUS_MODEL=$selected_model \
        ANTHROPIC_DEFAULT_SONNET_MODEL=$selected_model \
        ANTHROPIC_DEFAULT_HAIKU_MODEL="hf:zai-org/GLM-4.7-Flash" \
        CLAUDE_CODE_SUBAGENT_MODEL=$selected_model \
        CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1 \
        command $cmd $args
    end
end
