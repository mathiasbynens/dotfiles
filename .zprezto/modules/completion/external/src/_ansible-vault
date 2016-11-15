#compdef ansible-vault
# ------------------------------------------------------------------------------
# Copyright (c) 2016 Github zsh-users - http://github.com/zsh-users
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the zsh-users nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL ZSH-USERS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# ------------------------------------------------------------------------------
# Description
# -----------
#
#  Completion script for ansible v1.9.2 (http://ansible.org)
#
# ------------------------------------------------------------------------------
# Authors
# -------
#
#  * Rick van Hattem (https://github.com/wolph)
#
# ------------------------------------------------------------------------------
#

_ansible-vault-commands() {
  local -a commands
  
  commands=(
    'create:Create new encrypted file'
    'decrypt:Decrypt encrypted file'
    'edit:Edit encrypted file'
    'encrypt:Encrypt unencrypted file'
    'rekey:Change password for encrypted file'
    'view:View encrypted file'
  )
  
  _arguments -s : $nul_args && ret=0
  _describe -t commands 'ansible-vault command' commands && ret=0
}

_ansible-vault-command(){
  args=(
    '--debug[enable debugging]' \
    '--vault-password-file[vault password file]:password_file:_files'
    $nul_args
    "1::file_name:_files"
  )
  _arguments -s : $args && ret=0
}

_ansible-vault() {
  local -a nul_args
  nul_args=(
    '(-h --help)'{-h,--help}'[show help message and exit.]'
  )
  
  local curcontext=$curcontext ret=1
  
  if ((CURRENT == 2)); then
    _ansible-vault-commands
  else
    shift words
    (( CURRENT -- ))
    curcontext="${curcontext%:*:*}:ansible-vault-$words[1]:"
    _call_function ret _ansible-vault-command
  fi
}

_ansible-vault "$@"

# Local Variables:
# mode: Shell-Script
# sh-indentation: 2
# indent-tabs-mode: nil
# sh-basic-offset: 2
# End:
# vim: ft=zsh sw=2 ts=2 et
