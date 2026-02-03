function ai --description "Unified AI command interface"
    set -l cmd $argv[1]
    set -l args $argv[2..]

    if test -z "$cmd"
        __ai_show_help
        return 1
    end

    switch $cmd
        case cmd
            __ai_cmd $args
        case sum
            __ai_sum $args
        case gitmsg
            __ai_gitmsg $args
        case prdesc
            __ai_gitprdesc $args
        case explain
            __ai_explain $args
        case refactor
            __ai_refactor $args
        case review
            __ai_review $args
        case test
            __ai_test $args
        case docs
            __ai_docs $args
        case regex
            __ai_regex $args
        case sql
            __ai_sql $args
        case cmd-explain
            __ai_cmd_explain $args
        case cmd-fix
            __ai_cmd_fix $args
        case fmt
            __ai_fmt $args
        case proofread
            __ai_proofread $args
        case tone
            __ai_tone $args
        case tl
            __ai_translate $args
        case help "-h" "--help"
            __ai_show_help
        case '*'
            echo "Error: Unknown subcommand '$cmd'" >&2
            __ai_show_help
            return 1
    end
end

function __ai_cmd --description "Recommend a terminal command using AI"
    set system (grep ^NAME= /etc/os-release | cut -d '=' -f 2 | tr -d '"')
    set recommended_cmd (llm -t cmd -p os $system $argv)

    if test -z "$recommended_cmd"
        echo "Error: No command was generated." >&2
        return 1
    end

    echo "Recommended command:"
    echo "  $recommended_cmd"
    echo ""

    read -P "Do you want to run this command? (y/N) " confirm

    switch $confirm
        case 'y' 'Y' 'yes' 'YES'
            echo "Running: $recommended_cmd"
            eval $recommended_cmd
        case '*'
            echo "Command not executed."
            return 1
    end
end

function __ai_sum --description "Summarize content from a webpage or YouTube video using AI"
    if string match -qr 'youtube\.com|youtu\.be' -- $argv[1]
        set sub_url (yt-dlp -q --skip-download --convert-subs srt --write-sub --sub-langs "en" --write-auto-sub --print "requested_subtitles.en.url" "$argv[1]")
        set content (curl -s "$sub_url" | sed '/^$/d' | grep -v '^[0-9]*$' | grep -v '\-->' | sed 's/<[^>]*>//g' | tr '\n' ' ')
    else
        set content (curl -s $argv[1])
        set content (echo $content | strip-tags)
    end
    echo $content | llm --system "Summarize in bullet points"
end

function __ai_gitmsg --description "Create a git commit message using AI"
    argparse d/description -- $argv
    or return 1

    function __read_input
        set -l prompt $argv[1]
        read -P $prompt reply
        echo $reply
    end

    function __generate_commit_message
        PAGER="" git diff --minimal --cached | llm -t gitcommit
    end

    set commit_message (__generate_commit_message)

    while true
        set short_message (string split -m 1 "\n" $commit_message)[1]
        set -q _flag_description && set description (string split -m 1 "\n" $commit_message)[3]

        echo -e "Proposed commit message:\n$short_message\n"
        if set -q _flag_description
            echo -e "Proposed commit description:\n$description\n"
        end

        set choice (__read_input "Do you want to (a)ccept, (r)egenerate, or (c)ancel? (a/r/c) ")

        switch $choice
            case 'a' 'A' ''
                if set -q _flag_description
                    git commit $argv -m "$short_message" -m "$description"
                else
                    git commit $argv -m "$short_message"
                end
                if test $status -eq 0
                    echo "Changes committed successfully!"
                    return 0
                else
                    echo "Commit failed. Please check your changes and try again."
                    return 1
                end
            case 'r' 'R'
                echo "Regenerating commit message..."
                set commit_message (__generate_commit_message)
            case 'c' 'C' 'q' 'Q'
                echo "Commit cancelled."
                return 1
            case '*'
                echo "Invalid choice. Please try again."
        end
    end
end

function __ai_gitprdesc --description "Generate PR description from branch changes vs main"
    set branch_name (test -n "$argv[1]" && echo $argv[1] || git symbolic-ref --short HEAD 2>/dev/null)
    if test -z "$branch_name"
        echo "Not in a git repository branch"
        return 1
    end

    set diff_content (git diff main...$branch_name 2>/dev/null || git diff origin/main...$branch_name 2>/dev/null)

    if test -z "$diff_content"
        echo "No differences found between $branch_name and main"
        return
    end

    echo "Analyzing changes between $branch_name and main..."
    echo $diff_content | llm -t prdesc
end

function __ai_check_for_paths --description "Check if any argument is an existing path"
    for arg in $argv
        if test -e $arg
            return 0
        end
    end
    return 1
end

function __ai_validate_paths --description "Validate all args are existing paths, error if not"
    for arg in $argv
        if not test -e $arg
            echo "Error: '$arg' is not a file or directory. $cmd requires existing paths." >&2
            return 1
        end
    end
    return 0
end

function __ai_process_input --description "Process input using files-to-prompt or echo based on path detection"
    set -l template $argv[1]
    set -l extra_args $argv[2..]

    if __ai_check_for_paths $extra_args
        files-to-prompt $extra_args | llm -t $template
    else
        echo $extra_args | llm -t $template
    end
end

function __ai_explain --description "Explain code or file content"
    if test (count $argv) -gt 0
        __ai_process_input codeexplain $argv
    else
        llm -t codeexplain
    end
end

function __ai_refactor --description "Suggest code refactoring"
    if test (count $argv) -gt 0
        set cmd "Refactor"
        __ai_validate_paths $argv || return 1
        files-to-prompt $argv | llm -t refactor
    else
        llm -t refactor
    end
end

function __ai_review --description "Review code for issues"
    if test (count $argv) -gt 0
        set cmd "Review"
        __ai_validate_paths $argv || return 1
        files-to-prompt $argv | llm -t review
    else
        llm -t review
    end
end

function __ai_test --description "Generate tests from code"
    if test (count $argv) -gt 0
        set cmd "Test generation"
        __ai_validate_paths $argv || return 1
        files-to-prompt $argv | llm -t testgen
    else
        llm -t testgen
    end
end

function __ai_docs --description "Generate documentation from code"
    if test (count $argv) -gt 0
        set cmd "Documentation generation"
        __ai_validate_paths $argv || return 1
        files-to-prompt $argv | llm -t docs
    else
        llm -t docs
    end
end

function __ai_regex --description "Generate regex from natural language description"
    if test (count $argv) -eq 0
        echo "Error: No description provided." >&2
        echo "Usage: ai regex 'email addresses'" >&2
        return 1
    end
    llm -t regex $argv
end

function __ai_sql --description "Generate SQL from natural language description"
    if test (count $argv) -eq 0
        echo "Error: No description provided." >&2
        echo "Usage: ai sql 'users who signed up in last 30 days'" >&2
        return 1
    end
    echo "Generate SQL for: $argv" | llm -t sql
end

function __ai_cmd_explain --description "Explain what a shell command does"
    argparse l/last -- $argv
    or return 1

    if set -q _flag_last
        set cmd_to_explain (history --max 1)
        if test -z "$cmd_to_explain"
            echo "Error: No command found in history." >&2
            return 1
        end
        echo "Explaining last command: $cmd_to_explain"
    else if test (count $argv) -eq 0
        echo "Error: No command provided. Use --last to explain the previous command." >&2
        return 1
    else
        set cmd_to_explain "$argv"
    end

    echo "Explain this shell command: $cmd_to_explain" | llm -t cmdexplain
end

function __ai_cmd_fix --description "Suggest fixes for a failed command"
    argparse l/last -- $argv
    or return 1

    if set -q _flag_last
        set cmd_to_fix (history --max 1)
        if test -z "$cmd_to_fix"
            echo "Error: No command found in history." >&2
            return 1
        end
        echo "Analyzing last command: $cmd_to_fix"
    else if test (count $argv) -eq 0
        echo "Error: No command provided. Use --last to fix the previous command." >&2
        return 1
    else
        set cmd_to_fix "$argv"
    end

    echo "I ran this command and it failed: $cmd_to_fix" | llm -t cmdfix
end

function __ai_fmt --description "Format/reformat text"
    if test (count $argv) -gt 0
        __ai_process_input fmt $argv
    else
        llm -t fmt
    end
end

function __ai_proofread --description "Check grammar and spelling"
    if test (count $argv) -gt 0
        __ai_process_input proofread $argv
    else
        llm -t proofread
    end
end

function __ai_tone --description "Rewrite text with different tone"
    argparse t/tone= -- $argv
    or return 1
    set -q _flag_tone || set _flag_tone "professional"
    if test (count $argv) -gt 0
        if __ai_check_for_paths $argv
            files-to-prompt $argv | llm -t tone -p tone $_flag_tone
        else
            echo $argv | llm -t tone -p tone $_flag_tone
        end
    else
        llm -t tone -p tone $_flag_tone
    end
end

function __ai_translate --description "Translate text"
    argparse t/target= -- $argv
    or return 1
    set -q _flag_target || set _flag_target "spanish"
    if test (count $argv) -gt 0
        if __ai_check_for_paths $argv
            files-to-prompt $argv | llm -t translate -p target_lang $_flag_target
        else
            echo $argv | llm -t translate -p target_lang $_flag_target
        end
    else
        llm -t translate -p target_lang $_flag_target
    end
end

function __ai_show_help --description "Show ai command help"
    echo "ai - Unified AI command interface"
    echo ""
    echo "USAGE:"
    echo "  ai <subcommand> [arguments...]"
    echo ""
    echo "CODE ANALYSIS (files/directories only):"
    echo "  refactor     Suggest refactoring improvements"
    echo "  review       Review code for potential issues"
    echo "  test         Generate tests from code"
    echo "  docs         Generate documentation from code"
    echo ""
    echo "CODE GENERATION:"
    echo "  regex        Generate regex from natural language description"
    echo "  sql          Generate SQL from natural language description"
    echo ""
    echo "EXPLAIN & TEXT (files, directories, or text strings):"
    echo "  explain      Explain code, files, or text"
    echo "  fmt          Format/reformat text or files"
    echo "  proofread    Check grammar and spelling"
    echo "  tone         Rewrite with different tone (-t/--tone formal|casual|professional)"
    echo "  tl           Translate text (-t/--target spanish|french|...)"
    echo ""
    echo "COMMAND HELPERS:"
    echo "  cmd          Recommend a terminal command (prompts to run)"
    echo "  cmd-explain  Explain a shell command (--last/-l for previous command)"
    echo "  cmd-fix      Suggest fixes for failed command (--last/-l for previous command)"
    echo ""
    echo "GIT HELPERS:"
    echo "  gitmsg       Generate git commit message (-d for description)"
    echo "  prdesc       Generate PR description"
    echo ""
    echo "UTILITIES:"
    echo "  sum          Summarize webpage or YouTube video"
    echo "  help         Show this help message"
    echo ""
    echo "OPTIONS:"
    echo "  -h, --help   Show help message"
    echo ""
    echo "EXAMPLES:"
    echo "  ai explain 'what is recursion'"
    echo "  ai explain script.py src/"
    echo "  ai refactor function.js"
    echo "  ai regex 'extract email addresses'"
    echo "  ai sql 'users who signed up in last 30 days'"
    echo "  ai proofread 'Ths sentense has erors'"
    echo "  ai cmd 'find large files in current directory'"
    echo "  ai cmd-explain --last"
    echo "  ai cmd-fix --last"
    echo "  ai tone --tone formal 'Hey buddy, whats up?'"
    echo "  ai tl --target french hello.txt"
end
