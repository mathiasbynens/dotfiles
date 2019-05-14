function _pure_string_width \
    --description 'returns raw string length, i.e. ignore ANSI-color' \
    --argument-names prompt

    set --local empty ''
    set --local raw_prompt (string replace --all --regex '\e\[[^m]*m' $empty $prompt)

    string length $raw_prompt
end
