#!/bin/sh

# Source the files in the xinitrc.d directory
if [ -d /etc/X11/xinit/xinitrc.d ] ; then
    for f in /etc/X11/xinit/xinitrc.d/?*.sh ; do
        [ -x "$f" ] && . "$f"
    done
    unset f
fi

# Source the .Xresources file
# xrdb -merge ~/.Xresources

# Monitor Layout
xrandr --newmode "2560x1440_60.00" 311.83 2560 2744 3024 3488 1440 1441 1444 1490 && xrandr --addmode Virtual-1 "2560x1440_60.00" && xrandr --output Virtual-1 --mode 2560x1440_60.00

# Start the window manager
exec i3
