function _pure_parse_git_branch --description "Parse current Git branch name"
    begin
        git symbolic-ref --quiet --short HEAD; or \
        git describe --all --exact-match HEAD; or \
        git rev-parse --short HEAD; or '(unknown)'
      end ^/dev/null | sed -e 's|^refs/heads/||'
end
