# Main subcommands
complete --command ai --exclusive --condition __fish_use_subcommand --arguments cmd --description "Recommend a terminal command using AI"
complete --command ai --exclusive --condition __fish_use_subcommand --arguments sum --description "Summarize a webpage or YouTube video"
complete --command ai --exclusive --condition __fish_use_subcommand --arguments gitmsg --description "Generate git commit message"
complete --command ai --exclusive --condition __fish_use_subcommand --arguments prdesc --description "Generate PR description"
complete --command ai --exclusive --condition __fish_use_subcommand --arguments help --description "Show help message"

# Code analysis subcommands
complete --command ai --exclusive --condition __fish_use_subcommand --arguments explain --description "Explain code or file"
complete --command ai --exclusive --condition __fish_use_subcommand --arguments refactor --description "Suggest refactoring"
complete --command ai --exclusive --condition __fish_use_subcommand --arguments review --description "Review code for issues"
complete --command ai --exclusive --condition __fish_use_subcommand --arguments test --description "Generate tests"
complete --command ai --exclusive --condition __fish_use_subcommand --arguments docs --description "Generate documentation"

# Code generation subcommands
complete --command ai --exclusive --condition __fish_use_subcommand --arguments regex --description "Generate regex from natural language"
complete --command ai --exclusive --condition __fish_use_subcommand --arguments sql --description "Generate SQL from natural language"

# Command-related subcommands
complete --command ai --exclusive --condition __fish_use_subcommand --arguments cmd-explain --description "Explain a shell command"
complete --command ai --exclusive --condition __fish_use_subcommand --arguments cmd-fix --description "Suggest fixes for failed command"

# cmd-explain options
complete --command ai --exclusive --condition "__fish_seen_subcommand_from cmd-explain" --long last --short l --description "Use the last command from history"

# cmd-fix options
complete --command ai --exclusive --condition "__fish_seen_subcommand_from cmd-fix" --long last --short l --description "Use the last command from history"

# Text processing subcommands
complete --command ai --exclusive --condition __fish_use_subcommand --arguments fmt --description "Format/reformat text"
complete --command ai --exclusive --condition __fish_use_subcommand --arguments proofread --description "Check grammar and spelling"
complete --command ai --exclusive --condition __fish_use_subcommand --arguments tone --description "Rewrite with different tone"
complete --command ai --exclusive --condition __fish_use_subcommand --arguments tl --description "Translate text"

# gitmsg subcommand options
complete --command ai --exclusive --condition "__fish_seen_subcommand_from gitmsg" --long description --short d --description "Include commit description body"

# tone subcommand options
complete --command ai --exclusive --condition "__fish_seen_subcommand_from tone" --long tone --short t --description "Tone to use (formal, casual, concise, professional, friendly)" --require-parameter

# tl (translate) subcommand options
complete --command ai --exclusive --condition "__fish_seen_subcommand_from tl" --long target --short t --description "Target language" --require-parameter

# Global options
complete --command ai --exclusive --long help --short h --description "Show help message"
