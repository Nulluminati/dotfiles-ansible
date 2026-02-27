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

    # Fetch models from Synthetic.new API
    set -l models_json (curl -s https://api.synthetic.new/openai/v1/models)
    if test $status -ne 0
        echo "Error: Failed to fetch models from Synthetic.new API" >&2
        return 1
    end

    # Parse model data into arrays
    set -l model_ids (echo $models_json | jq -r '.data[].id')
    set -l model_names (echo $models_json | jq -r '.data[].name')

    # Use fzf to select model
    set -l selected_name (printf '%s\n' $model_names | fzf --prompt='Select model: ' --height=~50%)

    # Exit if user cancelled (Ctrl+C/Esc) or didn't select anything
    if test $status -ne 0 -o -z "$selected_name"
        return 1
    end

    # Find the model ID corresponding to the selected name
    set -l selected_model
    for i in (seq (count $model_names))
        if test "$model_names[$i]" = "$selected_name"
            set selected_model $model_ids[$i]
            break
        end
    end

    # Execute with selected model
    ANTHROPIC_BASE_URL=https://api.synthetic.new/anthropic \
    ANTHROPIC_AUTH_TOKEN="$SYNTHETIC_API_KEY" \
    ANTHROPIC_DEFAULT_OPUS_MODEL=$selected_model \
    ANTHROPIC_DEFAULT_SONNET_MODEL=$selected_model \
    ANTHROPIC_DEFAULT_HAIKU_MODEL=$selected_model \
    CLAUDE_CODE_SUBAGENT_MODEL=$selected_model \
    CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1 \
    command $cmd $args
end
