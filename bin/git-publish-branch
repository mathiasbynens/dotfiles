#!/usr/bin/env ruby

## git-publish-branch: a simple script to ease the unnecessarily complex
## task of "publishing" a branch, i.e., taking a local branch, creating a
## reference to it on a remote repo, and setting up the local branch to
## track the remote one, all in one go. you can even delete that remote
## reference.
##
## Usage: git publish-branch [-d] <branch> [repository]
##
## '-d' signifies deletion. <branch> is the branch to publish, and
## [repository] defaults to "origin". The remote branch name will be the
## same as the local branch name. Don't make life unnecessarily complex
## for yourself.
##
## Note that unpublishing a branch doesn't delete the local branch.
## Safety first!
##
## git-publish-branch Copyright 2008 William Morgan <wmorgan-git-wt-add@masanjin.net>. 
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or (at
## your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You can find the GNU General Public License at:
##   http://www.gnu.org/licenses/

def exec cmd
  puts cmd
  system cmd or abort unless $fake
end


head = `git symbolic-ref HEAD`.chomp.gsub(/refs\/heads\//, "")
delete = ARGV.delete "-d"
$fake = ARGV.delete "-n"
branch = (ARGV.shift || head).gsub(/refs\/heads\//, "")
remote = ARGV.shift || "origin"
local_ref = `git show-ref heads/#{branch}`
remote_ref = `git show-ref remotes/#{remote}/#{branch}`
remote_config = `git config branch.#{branch}.merge`

if delete
  ## we don't do any checking here because the remote branch might actually
  ## exist, whether we actually know about it or not.
  exec "git push #{remote} :refs/heads/#{branch}"

  unless local_ref.empty?
    exec "git config --unset branch.#{branch}.remote"
    exec "git config --unset branch.#{branch}.merge"
  end
else
  abort "No local branch #{branch} exists!" if local_ref.empty?
  abort "A remote branch #{branch} on #{remote} already exists!" unless remote_ref.empty?
  abort "Local branch #{branch} is already a tracking branch!" unless remote_config.empty?

  exec "git push #{remote} #{branch}:refs/heads/#{branch}"
  exec "git config branch.#{branch}.remote #{remote}"
  exec "git config branch.#{branch}.merge refs/heads/#{branch}"
end

