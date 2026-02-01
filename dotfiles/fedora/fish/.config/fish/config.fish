set -gx XDG_CACHE_HOME $HOME/.cache
set -gx XDG_CONFIG_HOME $HOME/.config
set -gx XDG_DATA_HOME $HOME/.local/share
set -gx XDG_DESKTOP_DIR $HOME/Desktop
set -gx XDG_DOWNLOAD_DIR $HOME/Downloads
set -gx XDG_DOCUMENTS_DIR $HOME/Documents
set -gx XDG_MUSIC_DIR $HOME/Music
set -gx XDG_PICTURES_DIR $HOME/Pictures
set -gx XDG_VIDEOS_DIR $HOME/Videos

set -gx KUBE_EDITOR nvim
set -gx VISUAL nvim
set -gx EDITOR nvim
set -gx BROWSER firefox
set -gx PAGER delta

set -gx nvm_default_version latest

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
