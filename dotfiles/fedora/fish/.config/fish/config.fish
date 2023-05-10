set -x VISUAL nvim
set -x EDITOR nvim
set -x BROWSER firefox
set -U fish_greeting ""

# Prompt - Starship
starship init fish | source
