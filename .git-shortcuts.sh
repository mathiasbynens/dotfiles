#straight up git status alias
alias gs='git status'
#status, but displayed in a more friendly/clean way
alias gss='git status -s'

#add all files
alias gaa='git add -A'


#git pull and push aliases
alias gp='git pull'
alias gph='git push'

#pull a specific branch/remote
function gp {
	gp "$1" "$2"
}

#pull a specific branch/remote
function gph {
	git push "$1" "$2"
}

#commit all files with message, and then display status
function gc {
	gaa
	git commit -m "$1"
	gs
}

#show local and current branch
alias gb='git branch'
#show remote branches
alias gbr='git branch -r'
#create new branch
alias gbn='git checkout -b'

#checkout branch
alias gck='git checkout'

#remove local branch
function gbdel {
	git branch -D "$1"
}
#delete remote branch
function gbrdel {
	git push origin :"$1"
}

#diff in color
alias gdiff='git diff --color-words'

#get a list of conflicts
alias conflicts='git diff --name-only --diff-filter=U'


alias gclean='git gc --prune=now && git remote prune origin'

#log of commits
alias glog='git log --graph --oneline --all --decorate'

#reset to head
alias gitreset='git reset --hard'
# reset to head and remove all untracked files (including npm installs)
alias gitreseteverything='git clean -d -x -f; git reset --hard'



if type git-up -t > /dev/null 2>&1; then
	alias gup='git-up'
	alias gupp='git-up && git push'
else
	alias gpr='git pull --rebase'
	alias gprp='gup && git push'
fi


#amend a commit by adding more files or changing the commit messge
function goops {
	git commit -a --amend -C HEAD
	gs
}


function gwut {
	echo "
- - - - - - - - - - - - - -
Git Convenience Shortcuts:
- - - - - - - - - - - - - -
gwut - List all Git Convenience commands and prompt symbols.
gs - git status
gaa - Add all changes (including untracted files) to staging
gc "Message" - Commit all new files & changes with message
goops - Add changes to previous commit & edit comessage
gp - Pull (via rebase) then push
gup - Pull (via rebase)
glog - Decorated & graphed log
gdiff - A word-diff of changes
gclean - Compress & garbage collect data store

- - - - - - - - - - - - - -
Prompt Symbols:
- - - - - - - - - - - - - -
The prompt shows the current branch & among other helpful things:

*  - Uncommitted changes
+  - Staged changes
%  - Untracked files
<  - You're behind the origin
>  - You're ahead of the origin
<> - You've diverged from the origin
=  - You're up-to-date with the origin

- - - - - - - - - - - - - -
"
}
