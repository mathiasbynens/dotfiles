#!/bin/bash

# crontest
#
# Test wrapper for cron tasks.  The suggested use is:
#
#  1. When adding your cron job, use all 5 stars to make it run every minute
#  2. Wrap the command in crontest
#        
#
#  Example:
#
#  $ crontab -e
#     * * * * * /usr/local/bin/crontest $HOME/bin/my-new-script --myparams
#
#  Now, cron will run your job every minute, but crontest will only allow one
#  instance to run at a time.  
#
#  crontest always wraps the command in "screen -D -m" if possible, so you can
#  use "screen -x" to attach and interact with the job.   
#
#  If --bashdb is used, the command line will be passed to bashdb.  Thus you
#  can attach with "screen -x" and debug the remaining command in context.
#
#  NOTES:
#  	- crontest can be used in other contexts, it doesn't have to be a cron job.
#  		Any place where commands are invoked without an interactive terminal and
#  		may need to be debugged.
#
#   - crontest writes its own stuff to /tmp/crontest.log
#
#   - If GNU screen isn't available, neither is --bashdb
#

crontestLog=/tmp/crontest.log
lockfile=$(if [[ -d /var/lock ]]; then echo /var/lock/crontest.lock; else echo /tmp/crontest.lock; fi )
useBashdb=false
useScreen=$( if which screen &>/dev/null; then echo true; else echo false; fi )
innerArgs="$@"
screenBin=$(which screen 2>/dev/null)

function errExit {
	echo "[-err-] $@" | tee -a $crontestLog >&2
}

function log {
	echo "[-stat-] $@" >> $crontestLog
}

function parseArgs {
	while [[ ! -z $1 ]]; do
		case $1 in
			--bashdb)
				if ! $useScreen; then
					errExit "--bashdb invalid in crontest because GNU screen not installed"
				fi
				if ! which bashdb &>/dev/null; then
					errExit "--bashdb invalid in crontest: no bashdb on the PATH"
				fi

				useBashdb=true
				;;
			--)
				shift
				innerArgs="$@"
				return 0
				;;
			*)
				innerArgs="$@"
				return 0
				;;
		esac
		shift
	done
}

if [[ -z  $sourceMe ]]; then
	# Lock the lockfile (no, we do not wish to follow the standard
	# advice of wrapping this in a subshell!)
	exec 9>$lockfile
	flock -n 9 || exit 1
	
	# Zap any old log data:
	[[ -f $crontestLog ]] && rm -f $crontestLog

	parseArgs "$@"

	log "crontest starting at $(date)"
	log "Raw command line: $@"
	log "Inner args: $@"
	log "screenBin: $screenBin"
	log "useBashdb: $( if $useBashdb; then echo YES; else echo no; fi )"
	log "useScreen: $( if $useScreen; then echo YES; else echo no; fi )"
	
	# Were building a command line.
	cmdline=""
	
	# If screen is available, put the task inside a pseudo-terminal
	# owned by screen.  That allows the developer to do a "screen -x" to
	# interact with the running command:
	if $useScreen; then
		cmdline="$screenBin -D -m -L"
	fi

	# If bashdb is installed and --bashdb is specified on the command line,
	# pass the command to bashdb.  This allows the developer to do a "screen -x" to
	# interactively debug a bash shell script:
	if $useBashdb; then
		cmdline="$cmdline $(which bashdb) "
	fi

	# Finally, append the target command and params:
	cmdline="$cmdline $innerArgs"

	log "cmdline: $cmdline"


	# And run the whole schlock:
	$cmdline 

	res=$?

	log "Command result: $res"


	echo "[-result-] $(if [[ $res -eq 0 ]]; then echo ok; else echo fail; fi)" >> $crontestLog

	# Release the lock:
	9<&-
fi


