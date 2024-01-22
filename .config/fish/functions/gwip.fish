function gwip --description 'git commit a work-in-progress branch'
    git add -u
    git rm (git ls-files --deleted) 2>/dev/null
    git commit -m "fixup chore(no-merge): work in progress" --no-verify
end
