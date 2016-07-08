# Source: https://gist.github.com/nolanlawson/8694399

_gradle()
{
  local cur=${COMP_WORDS[COMP_CWORD]}
  local gradle_cmd='gradle'
  if [[ -x ./gradlew ]]; then
    gradle_cmd='./gradlew'
  fi
  if [[ -x ../gradlew ]]; then
    gradle_cmd='../gradlew'
  fi

  local commands=''
  local cache_dir="$HOME/.gradle_tabcompletion"
  mkdir -p $cache_dir

  # TODO: include the gradle version in the checksum?  It's kinda slow
  #local gradle_version=$($gradle_cmd --version --quiet --no-color | grep '^Gradle ' | sed 's/Gradle //g')
  
  local gradle_files_checksum='';
  if [[ -f build.gradle ]]; then # top-level gradle file
    if [[ -x `which md5 2> /dev/null` ]]; then # mac
      local all_gradle_files=$(find . -name build.gradle 2>/dev/null)
      gradle_files_checksum=$(md5 -q -s "$(md5 -q $all_gradle_files)")
    else # linux
      gradle_files_checksum=($(find . -name build.gradle | xargs md5sum | md5sum))
    fi
  else # no top-level gradle file
    gradle_files_checksum='no_gradle_files'
  fi
  if [[ -f $cache_dir/$gradle_files_checksum ]]; then # cached! yay!
    commands=$(cat $cache_dir/$gradle_files_checksum)
  else # not cached! boo-urns!
    commands=$($gradle_cmd --no-color --quiet tasks | grep ' - ' | awk '{print $1}' | tr '\n' ' ')
    if [[ ! -z $commands ]]; then
      echo $commands > $cache_dir/$gradle_files_checksum
    fi
  fi
  COMPREPLY=( $(compgen -W "$commands" -- $cur) )
}
complete -F _gradle gradle
complete -F _gradle gradlew
complete -F _gradle ./gradlew
