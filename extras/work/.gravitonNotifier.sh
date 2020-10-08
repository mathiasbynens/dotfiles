#!/bin/bash

notify_pushover() {
    if [ $# -ne 3 ]; then
    cat <<- EOF
        Usage: $0 <title> <priority> <message>
EOF
        exit 1
    fi

    curl -s \
    --form-string "token=ac7xvh2zrrmiv6nxqoxgjerm1hsian" \
    --form-string "user=u71pdbtm2a917erqqijm6mkbror2ht" \
    --form-string "title=$1" \
    --form-string "priority=$2" \
    --form-string "message=$3" \
    https://api.pushover.net/1/messages.json &>/dev/null
}

graviton_monitor(){
    SECONDS=0
    graviton_pid=$1

    echo "Started @ $(date)"
    echo "Monitoring graviton deploy process $graviton_pid"

    # checking if graviton running
    while kill -0 $graviton_pid 2> /dev/null; do
        # graviton running
        sleep 10s
    done 
    
    cur_dir=${PWD##*/}

    # Retrieve the graviton deploy status
    graviton_status=$(grep "Running deploy finished successfully" graviton-deploy.log &>/dev/null && echo "Success" || echo "Failure or Other")

    if [[ $graviton_status =~ Success ]]; then
        priority=0
    else
        priority=1
    fi
    
    duration=$SECONDS
    duration_msg="$(($duration / 60)) minutes and $(($duration % 60)) seconds elapsed."

    #message=$(echo -e "$cur_dir [status]: $graviton_status \ncheck log for additional details.")
    message=$(echo -e "[solution]: $cur_dir \n[status]: $graviton_status \n\n$duration_msg \nCheck log for more details")
    echo $message
    
    notify_pushover "Graviton Deploy Finished" $priority "$message"
    echo "Deploy Finished @ $(date)"
    echo "Notification sent"
}

graviton_monitor $1