# -------------------------------------------------------------------------------------------------
# Copyright (c) 2015 zsh-syntax-highlighting contributors
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification, are permitted
# provided that the following conditions are met:
#
#  * Redistributions of source code must retain the above copyright notice, this list of conditions
#    and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright notice, this list of
#    conditions and the following disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of the zsh-syntax-highlighting contributors nor the names of its contributors
#    may be used to endorse or promote products derived from this software without specific prior
#    written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
# OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# -------------------------------------------------------------------------------------------------
# -*- mode: zsh; sh-indentation: 2; indent-tabs-mode: nil; sh-basic-offset: 2; -*-
# vim: ft=zsh sw=2 ts=2 et
# -------------------------------------------------------------------------------------------------

ZSH_HIGHLIGHT_STYLES[single-hyphen-option]=$unused_highlight
# Tests three codepaths:
# * -i  (no argument)
# * -C3 (pasted argument)
# * -u otheruser (non-pasted argument)
BUFFER='sudo -C3 -u otheruser -i ls /; sudo ; sudo -u ;'

expected_region_highlight=(
  "1 4 $ZSH_HIGHLIGHT_STYLES[precommand]" # sudo
  "6 8 $ZSH_HIGHLIGHT_STYLES[single-hyphen-option]" # -C3
  "10 11 $ZSH_HIGHLIGHT_STYLES[single-hyphen-option]" # -u
  "13 21 $ZSH_HIGHLIGHT_STYLES[default]" # otheruser
  "23 24 $ZSH_HIGHLIGHT_STYLES[single-hyphen-option]" # -i
  "26 27 $ZSH_HIGHLIGHT_STYLES[command]" # ls
  "29 29 $ZSH_HIGHLIGHT_STYLES[path]" # /
  "37 37 $ZSH_HIGHLIGHT_STYLES[unknown-token]" # ;, error because empty command
  "47 47 $ZSH_HIGHLIGHT_STYLES[unknown-token]" # ;, error because incomplete command
)
