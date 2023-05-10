function l; command exa -Flagh --sort name --git --icons --group-directories-first $argv; end
function ll; command exa -Flagh --git --icons --group-directories-first --sort modified $argv; end
function la; command exa -Fla --icons; end
function tree; command exa --tree --icons $argv; end
