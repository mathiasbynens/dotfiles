
function fi --description "Locate a file"
	locate . | fzf --query "$argv"
end