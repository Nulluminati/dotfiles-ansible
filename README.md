```
 _____     ______     ______   ______   __     __         ______     ______    
/\  __-.  /\  __ \   /\__  _\ /\  ___\ /\ \   /\ \       /\  ___\   /\  ___\   
\ \ \/\ \ \ \ \/\ \  \/_/\ \/ \ \  __\ \ \ \  \ \ \____  \ \  __\   \ \___  \  
 \ \____-  \ \_____\    \ \_\  \ \_\    \ \_\  \ \_____\  \ \_____\  \/\_____\ 
  \/____/   \/_____/     \/_/   \/_/     \/_/   \/_____/   \/_____/   \/_____/  
```

## table of contents
 - [introduction](#dotfiles)
 - [tools](#tools)
 - [installation](#installation)
 - [previews](#previews)
 - [license](#license)


# Dotfiles

> _"This is my dotfiles. There are many others like it, but this one is mine. My dotfiles is my best friend. It is my life. I must master it as I must master my life. Without me, my dotfiles is useless. Without my dotfiless, I am useless."_

Ansible is used to drive the management of my dotfiles as I am often setting up new development VM's in my homelab.

Ansible and Stow make up the underlying of this repository and how my dotfiles are deployed. Every package directory in `dotfiles/fedora` (or `dotfiles/mac` on macOS) is stowed by the `stow` role, so after the first ansible run each config is symlinked into `~`. Configs used on both platforms live in `dotfiles/shared`, and the per-platform packages symlink into it.

Fedora is the primary target. macOS is also supported: Homebrew installs the packages and casks, and `dotfiles/mac` is stowed into place.

## Tools

The important stuff:

Desktop (Fedora)
- i3
- Picom
- Polybar
- Pywal
- Rofi

Terminal
- Alacritty
- Ghostty
- Fish Shell
- Starship
- Yazi

Editors
- Neovim
- Sublime Text

AI tooling
- Claude Code
- Codex
- Pi
- Herdr, plus the local plugins in `herdr-plugins/`
- Hunk
- llm

The full package lists are much longer, see [CLI Tools](https://github.com/nulluminati/dotfiles-ansible/blob/main/roles/cli/defaults/main.yml) and [AI Tooling](https://github.com/nulluminati/dotfiles-ansible/blob/main/roles/ai_tooling/defaults/main.yml).

Font is Hack Nerd Font.

## Installation
⚠️ Do NOT run the setup script if you do not fully understand what this project does ⚠️

Prerequisites: `python3` and [uv](https://docs.astral.sh/uv/). The setup script installs Ansible with uv if it is missing.

1. Copy `secrets.example.yml` to `secrets.yml` and fill in the API keys you use
2. Run `./bin/setup`

Individual roles can be run with tags: `./bin/setup -t "fonts,cli"`. Run `./bin/setup -h` for help.

`bin/setup` has no dry-run flag. To preview changes, run Ansible directly:

```bash
ansible-playbook bootstrap.yml --extra-vars @secrets.yml -i hosts --check --tags "cli" --ask-become-pass
```


## Previews
🧛
![](https://github.com/nulluminati/dotfiles-ansible/blob/main/previews/preview.png?raw=true)


## License
<p align="center">
	<img src="https://kopimi.com/wp-content/uploads/2023/04/kopimi_text.gif" alt="Kopimi Logo" align="center" width="450">
</p>
<p align="center">
  <a href="https://kopimi.com/">✨ kopimi ✨</a>
</p>
<p align="center">
  I encourage you to fork, modify, change, share, or do whatever you want with this repository! Have fun!
</p>
