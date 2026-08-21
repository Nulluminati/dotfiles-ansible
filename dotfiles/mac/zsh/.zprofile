# ~/.zprofile — login-shell setup (runs once at login, before .zshrc).
# Homebrew shell environment (PATH, MANPATH, INFOPATH) for Apple Silicon.
eval "$(/opt/homebrew/bin/brew shellenv)"

# Leave self-updating casks alone. Apps with `auto_updates true` ship their own
# updater; when brew also tries to replace the bundle it fights that updater and
# fails on SIP-protected app bundles in /Applications.
export HOMEBREW_NO_UPGRADE_AUTO_UPDATES_CASKS=1
