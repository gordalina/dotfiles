autoload -Uz compinit

if [[ -n ${ZDOTDIR}/.zcompdump(#qN.mh+24) ]]; then
  compinit          # full run + rebuild once/day
else
  compinit -C       # trust cache, skip audit
fi