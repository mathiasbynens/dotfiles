if [[ ! -o interactive ]]; then
    return
fi

compctl -K _dotf dotf

_dotf() {
  local word words completions
  read -cA words
  word="${words[2]}"

  if [ "${#words}" -eq 2 ]; then
    completions="$(dotf commands)"
  else
    completions="$(dotf completions "${word}")"
  fi

  reply=("${(ps:\n:)completions}")
}
