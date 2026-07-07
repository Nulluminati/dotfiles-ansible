# ~/.zshrc — interactive shell configuration
# Managed via Ansible + Stow (dotfiles-ansible).
# Machine-local secrets and overrides go in ~/.zshrc.local (see bottom).

# ── Oh My Zsh ──────────────────────────────────────────────────────────
export ZSH="$HOME/.oh-my-zsh"
# Prompt is rendered by Starship (see "Prompt" below), so leave the omz theme empty.
ZSH_THEME=""

# Don't mark untracked files under VCS as dirty — much faster status checks
# in large repositories.
DISABLE_UNTRACKED_FILES_DIRTY="true"

# Keep this list lean; too many plugins slow down shell startup.
plugins=(git colored-man-pages colorize pip python brew macos aws heroku helm kubectl terraform kubectx docker docker-compose gh)

source "$ZSH/oh-my-zsh.sh"

# ── PATH ───────────────────────────────────────────────────────────────
export PATH="$PATH:$HOME/bin"
export PATH="$PATH:$HOME/.local/bin"
export PATH="/opt/homebrew/opt/postgresql@17/bin:$PATH"

# ── Version & language managers ────────────────────────────────────────
source /opt/homebrew/opt/chruby/share/chruby/chruby.sh
source /opt/homebrew/opt/chruby/share/chruby/auto.sh
command -v pyenv >/dev/null && eval "$(pyenv init -)"
eval "$(mise activate zsh)"

# Bun
export BUN_INSTALL="$HOME/.bun"
export PATH="$BUN_INSTALL/bin:$PATH"
[ -s "$HOME/.bun/_bun" ] && source "$HOME/.bun/_bun"

# ── Environment ────────────────────────────────────────────────────────
# Preferred editor; `subl -w` blocks git/kubectl until the Sublime tab closes.
export EDITOR='subl -w'
export VISUAL='subl -w'
export KUBE_EDITOR='subl -w'
export PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
export PUPPETEER_EXECUTABLE_PATH="$(which chromium)"
export DISABLE_SPRING=true
export LEFTHOOK_BIN=bin/lefthook

# ── Aliases ────────────────────────────────────────────────────────────
alias cl='clear'
alias kn='kubectl config set-context --current --namespace '
# Run claude with the Opus model by default
alias claude='claude --model opus'

# Ported from the Fedora fish config (conf.d/abbr.fish + functions/_alias.fish).
# Note: cat→bat, grep→color, top→htop, vi/vim→nvim, tree→eza intentionally
# override the originals, matching the fish setup.
alias cat='bat'
alias grep='grep --color=auto'
alias symlink='ln -s'
alias top='htop'
alias vi='nvim'
alias vim='nvim'
alias nmux='tmux new -s base'
alias tkill='tmux kill-session -t'

# eza-based listing (modern ls)
alias l='eza -laghF --git --icons --group-directories-first --sort name'
alias ll='eza -laghF --git --icons --group-directories-first --sort modified'
alias la='eza -laF --icons'
alias tree='eza --tree --icons'

# Directory jumps (paths adjusted for macOS; code lives under ~/personal)
alias config='cd ~/.config'
alias dls='cd ~/Downloads'
alias dots='cd ~/personal/dotfiles-ansible'
alias projects='cd ~/personal'

# Open changed git files in Sublime Text. No `xargs -r` needed — macOS xargs
# skips the command on empty input, so a clean tree is a no-op.
gsubl()  { git ls-files --modified --others --exclude-standard | xargs subl "$@"; }  # modified + untracked
gsubla() { git status --short | cut -c4- | xargs subl "$@"; }                        # staged + unstaged + untracked
gsubld() { git diff --name-only HEAD | xargs subl "$@"; }                            # changed vs HEAD

# ── Prompt ─────────────────────────────────────────────────────────────
# Cross-shell prompt; config at ~/.config/starship.toml (shared/starship).
eval "$(starship init zsh)"

# ── Machine-local overrides ────────────────────────────────────────────
# Never committed to git; hand-placed per machine (see .gitignore).
[ -f "$HOME/.zshrc.local" ] && source "$HOME/.zshrc.local"

# ── Interactive UX plugins ─────────────────────────────────────────────
# Installed via Homebrew (managed by the cli role); guarded so a machine
# without them yet won't error. Syntax-highlighting MUST be sourced last —
# it wraps ZLE widgets, so everything else has to be defined first.
[ -f /opt/homebrew/share/zsh-autosuggestions/zsh-autosuggestions.zsh ] && source /opt/homebrew/share/zsh-autosuggestions/zsh-autosuggestions.zsh
[ -f /opt/homebrew/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh ] && source /opt/homebrew/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
