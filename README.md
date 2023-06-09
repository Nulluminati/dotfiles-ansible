```
      :::::::::       ::::::::   :::::::::::       ::::::::::       :::::::::::       :::        ::::::::::       :::::::: 
     :+:    :+:     :+:    :+:      :+:           :+:                  :+:           :+:        :+:             :+:    :+: 
    +:+    +:+     +:+    +:+      +:+           +:+                  +:+           +:+        +:+             +:+         
   +#+    +:+     +#+    +:+      +#+           :#::+::#             +#+           +#+        +#++:++#        +#++:++#++   
  +#+    +#+     +#+    +#+      +#+           +#+                  +#+           +#+        +#+                    +#+    
 #+#    #+#     #+#    #+#      #+#           #+#                  #+#           #+#        #+#             #+#    #+#     
#########       ########       ###           ###              ###########       ########## ##########       ########       
```

## table of contents
 - [introduction](#Dotfiles)
 - [tools](#Toolss)
 - [installation](#Installation)
 - [previews](#previews)
 - [license](#license)


# Dotfiles

> _"This is my dotfiles. There are many others like it, but this one is mine. My dotfiles is my best friend. It is my life. I must master it as I must master my life. Without me, my dotfiles is useless. Without my dotfiless, I am useless."_

These dotfiles are intended for use with Fedora. macOS support is planned at some point.

## Tools

The important stuff:
- Alacritty
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
- TLDR : `./bin/setup`

Individual ansible tasks can be run with tags `ansible-playbook bootstrap.yml --tags "fonts"`

Ansible and Stow make up the underlying of this repository and how my dotfiles are deployed. Dotfiles within `dotfiles/fedora` are all managed by stow and after the initial ansible run will be symlinked to their respective config paths.

## Previews


## License
![kopimi logo](https://kopimi.com/wp-content/uploads/2023/04/kopimi_text.gif)
[kopimi](https://kopimi.com/)
I encourage you to fork, modify, change, share, or do whatever you want with this repository! Have fun!