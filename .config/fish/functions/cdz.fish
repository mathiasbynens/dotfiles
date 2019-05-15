function cdz --description 'Change to a directory using fuzzy finder. (Usually found as fd)'

	if test (count $argv) -gt 1
		echo "fd only accepts 1 argument, (count $argv) given"
		return 1
	end

	if test -n $argv
		echo $argv | sed -ne 's/\(.*\/\)\?\(.*\)/\1/p' | read base
		echo $argv | sed -ne 's/\(.*\/\)\?\(.*\)/\2/p' | read query

		if test -z "$base"; or not set -q base
			set base .
		end
	else
		set base .
		set query ''
	end

	# TODO. this can probably be improved ot use locate instead, e.g.
	#    file="$(locate -Ai -0 $@ | grep -z -vE '~$' | fzf --read0 -0 -1)"
	# from https://github.com/junegunn/fzf/wiki/examples
	find $base -type d -path '*/\.*' -prune -o -type d -print ^ /dev/null | fzf +m --query=$query --select-1 --exit-0 > $TMPDIR/dirs

	set dir (cat $TMPDIR/dirs)

	if test -n "$dir"
		cd "$dir"
	end

end