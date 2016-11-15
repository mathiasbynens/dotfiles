#!/usr/bin/env zsh

#
# zsh-async
#
# version: 1.1.0
# author: Mathias Fredriksson
# url: https://github.com/mafredri/zsh-async
#

# Wrapper for jobs executed by the async worker, gives output in parseable format with execution time
_async_job() {
	# Store start time as double precision (+E disables scientific notation)
	float -F duration=$EPOCHREALTIME

	# Run the command
	#
	# What is happening here is that we are assigning stdout, stderr and ret to
	# variables, and then we are printing out the variable assignment through
	# typeset -p. This way when we run eval we get something along the lines of:
	# 	eval "
	# 		typeset stdout=' M async.test.sh\n M async.zsh'
	# 		typeset ret=0
	# 		typeset stderr=''
	# 	"
	unset stdout stderr ret
	eval "$(
		{
			stdout=$(eval "$@")
			ret=$?
			typeset -p stdout ret
		} 2> >(stderr=$(cat); typeset -p stderr)
	)"

	# Calculate duration
	duration=$(( EPOCHREALTIME - duration ))

	# stip all null-characters from stdout and stderr
	stdout=${stdout//$'\0'/}
	stderr=${stderr//$'\0'/}

	# if ret is missing for some unknown reason, set it to -1 to indicate we
	# have run into a bug
	ret=${ret:--1}

	# Grab mutex lock
	read -ep >/dev/null

	# return output (<job_name> <return_code> <stdout> <duration> <stderr>)
	print -r -N -n -- "$1" "$ret" "$stdout" "$duration" "$stderr"$'\0'

	# Unlock mutex
	print -p "t"
}

# The background worker manages all tasks and runs them without interfering with other processes
_async_worker() {
	local -A storage
	local unique=0

	# Process option parameters passed to worker
	while getopts "np:u" opt; do
		case $opt in
			# Use SIGWINCH since many others seem to cause zsh to freeze, e.g. ALRM, INFO, etc.
			n) trap 'kill -WINCH $ASYNC_WORKER_PARENT_PID' CHLD;;
			p) ASYNC_WORKER_PARENT_PID=$OPTARG;;
			u) unique=1;;
		esac
	done

	# Create a mutex for writing to the terminal through coproc
	coproc cat
	# Insert token into coproc
	print -p "t"

	while read -r cmd; do
		# Separate on spaces into an array
		cmd=(${=cmd})
		local job=$cmd[1]

		# Check for non-job commands sent to worker
		case $job in
			_unset_trap)
				trap - CHLD; continue;;
			_killjobs)
				# Do nothing in the worker when receiving the TERM signal
				trap '' TERM
				# Send TERM to the entire process group (PID and all children)
				kill -TERM -$$ &>/dev/null
				# Reset trap
				trap - TERM
				continue
				;;
		esac

		# If worker should perform unique jobs
		if (( unique )); then
			# Check if a previous job is still running, if yes, let it finnish
			for pid in ${${(v)jobstates##*:*:}%\=*}; do
				if [[ ${storage[$job]} == $pid ]]; then
					continue 2
				fi
			done
		fi

		# Run task in background
		_async_job $cmd &
		# Store pid because zsh job manager is extremely unflexible (show jobname as non-unique '$job')...
		storage[$job]=$!
	done
}

#
#  Get results from finnished jobs and pass it to the to callback function. This is the only way to reliably return the
#  job name, return code, output and execution time and with minimal effort.
#
# usage:
# 	async_process_results <worker_name> <callback_function>
#
# callback_function is called with the following parameters:
# 	$1 = job name, e.g. the function passed to async_job
# 	$2 = return code
# 	$3 = resulting stdout from execution
# 	$4 = execution time, floating point e.g. 2.05 seconds
# 	$5 = resulting stderr from execution
#
async_process_results() {
	setopt localoptions noshwordsplit

	integer count=0
	local worker=$1
	local callback=$2
	local -a items
	local IFS=$'\0'

	typeset -gA ASYNC_PROCESS_BUFFER
	# Read output from zpty and parse it if available
	while zpty -rt $worker line 2>/dev/null; do
		# Remove unwanted \r from output
		ASYNC_PROCESS_BUFFER[$worker]+=${line//$'\r'$'\n'/$'\n'}
		# Split buffer on null characters, preserve empty elements
		items=("${(@)=ASYNC_PROCESS_BUFFER[$worker]}")
		# Remove last element since it's due to the return string separator structure
		items=("${(@)items[1,${#items}-1]}")

		# Continue until we receive all information
		(( ${#items} % 5 )) && continue

		# Work through all results
		while (( ${#items} > 0 )); do
			$callback "${(@)=items[1,5]}"
			shift 5 items
			count+=1
		done

		# Empty the buffer
		unset "ASYNC_PROCESS_BUFFER[$worker]"
	done

	# If we processed any results, return success
	(( count )) && return 0

	# No results were processed
	return 1
}

# Watch worker for output
_async_zle_watcher() {
	setopt localoptions noshwordsplit
	typeset -gA ASYNC_PTYS ASYNC_CALLBACKS
	local worker=$ASYNC_PTYS[$1]
	local callback=$ASYNC_CALLBACKS[$worker]

	if [[ -n $callback ]]; then
		async_process_results $worker $callback
	fi
}

#
# Start a new asynchronous job on specified worker, assumes the worker is running.
#
# usage:
# 	async_job <worker_name> <my_function> [<function_params>]
#
async_job() {
	setopt localoptions noshwordsplit

	local worker=$1; shift
	zpty -w $worker $@
}

# This function traps notification signals and calls all registered callbacks
_async_notify_trap() {
	setopt localoptions noshwordsplit

	for k in ${(k)ASYNC_CALLBACKS}; do
		async_process_results $k ${ASYNC_CALLBACKS[$k]}
	done
}

#
# Register a callback for completed jobs. As soon as a job is finnished, async_process_results will be called with the
# specified callback function. This requires that a worker is initialized with the -n (notify) option.
#
# usage:
# 	async_register_callback <worker_name> <callback_function>
#
async_register_callback() {
	setopt localoptions noshwordsplit nolocaltraps

	typeset -gA ASYNC_CALLBACKS
	local worker=$1; shift

	ASYNC_CALLBACKS[$worker]="$*"

	if (( ! ASYNC_USE_ZLE_HANDLER )); then
		trap '_async_notify_trap' WINCH
	fi
}

#
# Unregister the callback for a specific worker.
#
# usage:
# 	async_unregister_callback <worker_name>
#
async_unregister_callback() {
	typeset -gA ASYNC_CALLBACKS

	unset "ASYNC_CALLBACKS[$1]"
}

#
# Flush all current jobs running on a worker. This will terminate any and all running processes under the worker, use
# with caution.
#
# usage:
# 	async_flush_jobs <worker_name>
#
async_flush_jobs() {
	setopt localoptions noshwordsplit

	local worker=$1; shift

	# Check if the worker exists
	zpty -t $worker &>/dev/null || return 1

	# Send kill command to worker
	zpty -w $worker "_killjobs"

	# Clear all output buffers
	while zpty -r $worker line; do true; done

	# Clear any partial buffers
	typeset -gA ASYNC_PROCESS_BUFFER
	unset "ASYNC_PROCESS_BUFFER[$worker]"
}

#
# Start a new async worker with optional parameters, a worker can be told to only run unique tasks and to notify a
# process when tasks are complete.
#
# usage:
# 	async_start_worker <worker_name> [-u] [-n] [-p <pid>]
#
# opts:
# 	-u unique (only unique job names can run)
# 	-n notify through SIGWINCH signal
# 	-p pid to notify (defaults to current pid)
#
async_start_worker() {
	setopt localoptions noshwordsplit

	local worker=$1; shift
	zpty -t $worker &>/dev/null && return

	typeset -gA ASYNC_PTYS
	typeset -h REPLY
	zpty -b $worker _async_worker -p $$ $@ || {
		async_stop_worker $worker
		return 1
	}

	if (( ASYNC_USE_ZLE_HANDLER )); then
		ASYNC_PTYS[$REPLY]=$worker
		zle -F $REPLY _async_zle_watcher

		# If worker was called with -n, disable trap in favor of zle handler
		async_job $worker _unset_trap
	fi
}

#
# Stop one or multiple workers that are running, all unfetched and incomplete work will be lost.
#
# usage:
# 	async_stop_worker <worker_name_1> [<worker_name_2>]
#
async_stop_worker() {
	setopt localoptions noshwordsplit

	local ret=0
	for worker in $@; do
		# Find and unregister the zle handler for the worker
		for k v in ${(@kv)ASYNC_PTYS}; do
			if [[ $v == $worker ]]; then
				zle -F $k
				unset "ASYNC_PTYS[$k]"
			fi
		done
		async_unregister_callback $worker
		zpty -d $worker 2>/dev/null || ret=$?
	done

	return $ret
}

#
# Initialize the required modules for zsh-async. To be called before using the zsh-async library.
#
# usage:
# 	async_init
#
async_init() {
	(( ASYNC_INIT_DONE )) && return
	ASYNC_INIT_DONE=1

	zmodload zsh/zpty
	zmodload zsh/datetime

	# Check if zsh/zpty returns a file descriptor or not, shell must also be interactive
	ASYNC_USE_ZLE_HANDLER=0
	[[ -o interactive ]] && {
		typeset -h REPLY
		zpty _async_test cat
		(( REPLY )) && ASYNC_USE_ZLE_HANDLER=1
		zpty -d _async_test
	}
}

async() {
	async_init
}

async "$@"
