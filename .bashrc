[ -n "$PS1" ] && source ~/.bash_profile;

countdown(){
    date1=$((`date +%s` + $1));
    while [ "$date1" -ge `date +%s` ]; do 
    ## Is this more than 24h away?
    days=$(($(($(( $date1 - $(date +%s))) * 1 ))/86400))
    echo -ne "$(date -ju -f %s $(($date1 - `date +%s`)) +%H:%M:%S)\r";
    sleep 0.1
    done
    afplay /System/Library/Sounds/Glass.aiff -v 10
}

stopwatch(){
  date1=`date +%s`;
   while true; do
    echo -ne "$(date -ju -f %s $(($date1 - `date +%s`)) +%H:%M:%S)\r";
    sleep 0.1
   done
  afplay /System/Library/Sounds/Glass.aiff -v 5
}

pomodoro(){
    for i in 1 2 3 4
    do
      echo "Pomodoro $i";
      countdown 60*25;
      echo "5 min Break";
      countdown 60*5;
    done
    echo "Long Break";
    countdown 60*25;
}

. "$HOME/.cargo/env"
