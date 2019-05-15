function __last_command_duration
  if [ $CMD_DURATION ]
    if test $CMD_DURATION -gt $pure_cmd_max_exec_time
      echo ⏳ (__format_time $CMD_DURATION $pure_command_max_exec_time)
    end
  end
end