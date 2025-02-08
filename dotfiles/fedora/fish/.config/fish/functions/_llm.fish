function llmmodel --description "Set model for AI commands"
    llm models default $argv
end

function llmchat --description "Chat with AI"
	llm chat
end

function llmcmd --description "Recommend a terminal command using AI"
    set system (grep ^NAME= /etc/os-release | cut -d '=' -f 2 | tr -d '"')
    llm -t cmd -p os $system $argv
end

function llmgitmsg --description "Create a git commit message using AI"
    argparse d/description -- $argv
    or return 1

    function read_input
        set -l prompt $argv[1]
        read -P $prompt reply
        echo $reply
    end
	
	function generate_commit_message
		PAGER="" git diff --minimal --cached | llm -t gitcommit
	end

    set commit_message (generate_commit_message)

    while true
        # Extract message components based on description flag
        set short_message (string split -m 1 "\n" $commit_message)[1]
        set -q _flag_description && set description (string split -m 1 "\n" $commit_message)[3]

        echo -e "Proposed commit message:\n$short_message\n"

        if set -q _flag_description
            echo -e "Proposed commit description:\n$description\n"
        end

        set choice (read_input "Do you want to (a)ccept, (r)egenerate, or (c)ancel? (a/r/c) ")

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
                set commit_message (generate_commit_message)
            case 'c' 'C' 'q' 'Q'
                echo "Commit cancelled."
                return 1
            case '*'
                echo "Invalid choice. Please try again."
        end
    end
end

function llmwebsum --description "Summarize a webpage using AI"
	# Fetch a url with curl, strip tags to reduce tokens and send to llm
    set content (curl -s $argv)
    set trimmed_content (echo $content | strip-tags)
    echo $trimmed_content| llm --system "Summarize in bullet points"
end

function llmytsum --description "Summarize a YouTube video using AI"
    # Fetch subtitles with youtube-dl, strip tags to reduce tokens and send to llm
    set sub_url (yt-dlp -q --skip-download --convert-subs srt --write-sub --sub-langs "en" --write-auto-sub --print "requested_subtitles.en.url" "$argv")
    set content (curl -s "$sub_url" | sed '/^$/d' | grep -v '^[0-9]*$' | grep -v '\-->' | sed 's/<[^>]*>//g' | tr '\n' ' ')
    echo $content| llm --system "Summarize in bullet points"
end

function llmgitprdesc --description "Generate PR description from branch changes vs main"
    # Get branch name from argument or current branch
    set branch_name (test -n "$argv[1]" && echo $argv[1] || git symbolic-ref --short HEAD 2>/dev/null)
    if test -z "$branch_name"
        echo "Not in a git repository branch"
        return 1
    end

    # Get diff against main (fallback to origin/main)
    set diff_content (git diff main...$branch_name 2>/dev/null || git diff origin/main...$branch_name 2>/dev/null)

    if test -z "$diff_content"
        echo "No differences found between $branch_name and main"
        return
    end

    echo "Analyzing changes between $branch_name and main..."
    echo $diff_content | llm -t prdesc
end
