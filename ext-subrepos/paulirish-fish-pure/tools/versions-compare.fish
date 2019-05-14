set --global fail 1
set --global success 0

function fish_version_below \
    --description "Compare versions.  By default this tests \$FISH_VERSION, but if a second argument is provided it tests against that version." \
    --argument-names expected actual

	if test -z "$actual"
		set actual $FISH_VERSION
	end

    if test $expected = $actual
        return $fail
    end

    # busybox compatibility (see https://github.com/fish-shell/fish-shell/issues/4419#issuecomment-453512461)
	printf '%s\n' $actual $expected | sort -c -t. -k 1,1n -k 2,2n -k 3,3n 2> /dev/null

	return $status
end

function fish_version_at_least \
    --description "Compare versions.  By default this tests \$FISH_VERSION, but if a second argument is provided it tests against that version." \
    --argument-names expected actual

    not fish_version_below $argv >/dev/null

    return $status
end

function print_fish_version_below \
    --argument-names expected

    printf "%sonly fish <%s: %s" (set_color blue) $expected (set_color normal) 1>&2
end

function print_fish_version_at_least \
    --argument-names expected
    printf "%sonly fish <%s: %s" (set_color blue) $expected (set_color normal) 1>&2
end