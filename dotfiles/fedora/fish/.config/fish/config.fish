set -gx KUBE_EDITOR nvim
set -gx VISUAL nvim
set -gx EDITOR nvim
set -gx BROWSER firefox

set -U fish_greeting ""

# Prompt - Starship
starship init fish | source
