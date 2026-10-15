function opengo --description "Run pi with an OpenCode Go subscription model"
    # Query pi for the current opencode-go model list so this stays in sync
    # with pi releases without needing to update this file.
    set -l models (pi --list-models | awk 'NR > 1 && $1 == "opencode-go" {print $2}')
    if test -z "$models"
        echo "Error: No opencode-go models found via 'pi --list-models'" >&2
        return 1
    end

    set -l selected_model (printf '%s\n' $models | fzf --prompt='Select model: ' --height=~50%)

    if test $status -ne 0 -o -z "$selected_model"
        return 1
    end

    command pi --provider opencode-go --model $selected_model $argv
end
