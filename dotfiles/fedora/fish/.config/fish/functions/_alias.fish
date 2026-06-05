function grep --description "Grep with color"; command grep --color=auto $argv; end
function gsubl --description "Open modified and untracked files in Sublime Text"; git ls-files --modified --others --exclude-standard | xargs -r subl $argv; end
function gsubla --description "Open all changed files (staged, unstaged, untracked) in Sublime Text"; git status --short | cut -c4- | xargs -r subl $argv; end
function gsubld --description "Open files changed from HEAD (staged + unstaged) in Sublime Text"; git diff --name-only HEAD | xargs -r subl $argv; end
function l --description "List files with details, sorted by name"; command eza -laghF --git --icons --group-directories-first --sort name $argv; end
function ll --description "List files with details, sorted by modification time"; command eza -laghF --git --icons --group-directories-first --sort modified $argv; end
function la --description "List all files including hidden"; command eza -laF --icons; end
function tree --description "Show directory tree with icons"; command eza --tree --icons $argv; end
