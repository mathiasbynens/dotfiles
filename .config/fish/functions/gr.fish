
# git root
function gr --description "Jump to the git root"
	set -l repo_info (command git rev-parse --git-dir --is-inside-git-dir --is-bare-repository --is-inside-work-tree --short HEAD ^/dev/null)
  	test -n "$repo_info"; or return

	set -l cd_up_path (command git rev-parse --show-cdup)

	if test -n $cd_up_path
		cd $cd_up_path
	end
end
