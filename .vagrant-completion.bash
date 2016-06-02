#!/bin/bash

# Source: https://github.com/kura/vagrant-bash-completion

# (The MIT License)
#
# Copyright (c) 2014 Kura
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the 'Software'), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


__pwdln() {
   pwdmod="${PWD}/"
   itr=0
   until [[ -z "$pwdmod" ]];do
      itr=$(($itr+1))
      pwdmod="${pwdmod#*/}"
   done
   echo -n $(($itr-1))
}

__vagrantinvestigate() {
   if [ -n "$VAGRANT_CWD" ];then
     if [ -f "${VAGRANT_CWD}/.vagrant" -o -d "${VAGRANT_CWD}/.vagrant" ];then
        echo "${VAGRANT_CWD}/.vagrant"
        return 0
     fi
   fi
   if [ -f "${PWD}/.vagrant" -o -d "${PWD}/.vagrant" ];then
      echo "${PWD}/.vagrant"
      return 0
   else
      pwdmod2="${PWD}"
      for (( i=2; i<=$(__pwdln); i++ ));do
         pwdmod2="${pwdmod2%/*}"
         if [ -f "${pwdmod2}/.vagrant" -o -d "${pwdmod2}/.vagrant" ];then
            echo "${pwdmod2}/.vagrant"
            return 0
         fi
      done
   fi
   return 1
}

_vagrant() {
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    commands="snapshot box connect destroy docker-logs docker-run global-status halt help init list-commands login package plugin provision rdp reload resume rsync rsync-auto share ssh ssh-config status suspend up version"

    if [ $COMP_CWORD == 1 ]
    then
      COMPREPLY=($(compgen -W "${commands}" -- ${cur}))
      return 0
    fi

    if [ $COMP_CWORD == 2 ]
    then
        case "$prev" in
            "init")
                local box_list=$(find $HOME/.vagrant.d/boxes -mindepth 1 -maxdepth 1 -type d -exec basename {} \;|sed -e 's/-VAGRANTSLASH-/\//')
                COMPREPLY=($(compgen -W "${box_list}" -- ${cur}))
                return 0
                ;;
            "up")
                vagrant_state_file=$(__vagrantinvestigate) || return 1
                if [[ -d $vagrant_state_file ]]
                then
                    vm_list=$(find $vagrant_state_file/machines -mindepth 1 -maxdepth 1 -type d -exec basename {} \;)
                fi
                local up_commands="--no-provision"
                COMPREPLY=($(compgen -W "${up_commands} ${vm_list}" -- ${cur}))
                return 0
                ;;
            "ssh"|"provision"|"reload"|"halt"|"suspend"|"resume"|"ssh-config")
                vagrant_state_file=$(__vagrantinvestigate) || return 1
                if [[ -f $vagrant_state_file ]]
                then
                      running_vm_list=$(grep 'active' $vagrant_state_file | sed -e 's/"active"://' | tr ',' '\n' | cut -d '"' -f 2 | tr '\n' ' ')
                else
                      running_vm_list=$(find $vagrant_state_file -type f -name "id" | awk -F"/" '{print $(NF-2)}')
                fi
                COMPREPLY=($(compgen -W "${running_vm_list}" -- ${cur}))
                return 0
                ;;
            "box")
                box_commands="add help list remove repackage"
                COMPREPLY=($(compgen -W "${box_commands}" -- ${cur}))
                return 0
                ;;
            "plugin")
                plugin_commands="install license list uninstall update"
                COMPREPLY=($(compgen -W "${plugin_commands}" -- ${cur}))
                return 0
                ;;
            "help")
                COMPREPLY=($(compgen -W "${commands}" -- ${cur}))
                return 0
                ;;
            "snapshot")
                snapshot_commands="back delete go list take"
                COMPREPLY=($(compgen -W "${snapshot_commands}" -- ${cur}))
                return 0
                ;;
            *)
            ;;
        esac
    fi

    if [ $COMP_CWORD == 3 ]
    then
      action="${COMP_WORDS[COMP_CWORD-2]}"
      case "$action" in
          "up")
              if [ "$prev" == "--no-provision" ]; then
                  COMPREPLY=($(compgen -W "${vm_list}" -- ${cur}))
                  return 0
              fi
              ;;
          "box")
              case "$prev" in
                  "remove"|"repackage")
                      local box_list=$(find $HOME/.vagrant.d/boxes -mindepth 1 -maxdepth 1 -type d -exec basename {} \;|sed -e 's/-VAGRANTSLASH-/\//')
                      COMPREPLY=($(compgen -W "${box_list}" -- ${cur}))
                      return 0
                      ;;
                  *)
              esac
              ;;
          "snapshot")
              if [ "$prev" == "go" ]; then
                  local snapshot_list=$(vagrant snapshot list | awk '/Name:/ { print $2 }')
                  COMPREPLY=($(compgen -W "${snapshot_list}" -- ${cur}))
                  return 0
              fi
              ;;
      esac
    fi
}
complete -F _vagrant vagrant
