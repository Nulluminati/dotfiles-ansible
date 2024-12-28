function l; command eza -laghF --git --icons --group-directories-first --sort name $argv; end
function ll; command eza -laghF --git --icons --group-directories-first --sort modified $argv; end
function la; command eza -laF --icons; end
function tree; command eza --tree --icons $argv; end
