function llmchat --description "Chat with AI (claude-3.5-sonnet-latest)"
	llm chat -m claude-3.5-sonnet-latest
end

function llmgitmsg --description "Create a git commit message using AI"
	git add -A .

	function generate_commit_message
		git diff --minimal --cached | llm -t gitcommit
	end

    set commit_message (generate_commit_message $argv --retry "")

    while true
        echo -e "Proposed commit message:\n"
        echo $commit_message
        echo -e ""

        set choice (read_input "Do you want to (a)ccept or (r)egenerate? ")

		set short_message (string split -m 1 "\n" $commit_message)[1]
		set description (string split -m 1 "\n" $commit_message)[2]

		if test -z "$description"
			set description ""
		end

        switch $choice
            case 'a' 'A' ''
                if git commit $argv -m "$short_message" -m "$description"
                    echo "Changes committed successfully!"
                    return 0
                else
                    echo "Commit failed. Please check your changes and try again."
                    return 1
                end
            case 'r' 'R'
                echo "Regenerating commit message..."
                set commit_message (generate_commit_message $argv --retry $commit_message)
            case 'c' 'C' 'q' 'Q'
                echo "Commit cancelled."
                return 1
            case '*'
                echo "Invalid choice. Please try again."
        end
    end
end
