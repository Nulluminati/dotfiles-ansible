```
 _____     ______     ______   ______   __     __         ______     ______    
/\  __-.  /\  __ \   /\__  _\ /\  ___\ /\ \   /\ \       /\  ___\   /\  ___\   
\ \ \/\ \ \ \ \/\ \  \/_/\ \/ \ \  __\ \ \ \  \ \ \____  \ \  __\   \ \___  \  
 \ \____-  \ \_____\    \ \_\  \ \_\    \ \_\  \ \_____\  \ \_____\  \/\_____\ 
  \/____/   \/_____/     \/_/   \/_/     \/_/   \/_____/   \/_____/   \/_____/  
```

## table of contents
 - [introduction](#Dotfiles)
 - [tools](#Toolss)
 - [installation](#Installation)
 - [previews](#previews)
 - [license](#license)


# Dotfiles

> _"This is my dotfiles. There are many others like it, but this one is mine. My dotfiles is my best friend. It is my life. I must master it as I must master my life. Without me, my dotfiles is useless. Without my dotfiless, I am useless."_

Ansible is used to drive the management of my dotfiles as I am often setting up new development VM's in my homelab.

Ansible and Stow make up the underlying of this repository and how my dotfiles are deployed. Dotfiles within `dotfiles/fedora` are all managed by stow and after the initial ansible run will be symlinked to their respective config paths.

These dotfiles are intended for use with Fedora. macOS support is planned at some point.

## Tools

The important stuff:
- Alacritty
- Claude Code
- Fish Shell
- i3
- Picom
- Polybar
- Pywal
- Rofi
- Starship
- Sublime Text

The full list is much longer, see [CLI Tools](https://github.com/nulluminati/dotfiles-ansible/blob/main/roles/cli/tasks/fedora.yml)

Font is Hack Nerd Font.

## Installation
⚠️ Do NOT run the setup script if you do not fully understand what this project does ⚠️

- TLDR : `./bin/setup`

Individual ansible tasks can be run with tags `ansible-playbook bootstrap.yml --tags "fonts"`


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
