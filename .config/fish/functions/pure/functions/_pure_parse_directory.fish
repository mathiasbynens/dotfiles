function _pure_parse_directory \
    --description "Replace '$HOME' with '~'" \
    --argument-names max_path_length

    set --local folder (string replace $HOME '~' $PWD)
    
    if test -n "$max_path_length";
        if test (string length $folder) -gt $max_path_length;
            # If path exceeds maximum symbol limit, use default fish path formating function
            set folder (prompt_pwd)
        end
    end
    echo $folder
end
