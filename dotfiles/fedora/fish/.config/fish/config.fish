set -gx KUBE_EDITOR nvim
set -gx VISUAL nvim
set -gx EDITOR nvim
set -gx BROWSER firefox

set -U fish_greeting ""

# Source Multi-function files
source ~/.config/fish/functions/_alias.fish
source ~/.config/fish/functions/_llm.fish

# Start ssh agent
ssh_agent

# Starship
function starship_transient_prompt_func
    starship module character
end
starship init fish | source
enable_transience
