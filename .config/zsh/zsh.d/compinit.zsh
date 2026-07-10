autoload -Uz compinit

# Use a single dump file for both the freshness check and compinit itself.
# Rebuild (with the compaudit security scan) at most once a day; otherwise
# trust the cached dump and skip the audit.
zdump=${XDG_CACHE_HOME:-$HOME/.cache}/zsh/zcompdump
[[ -d ${zdump:h} ]] || mkdir -p ${zdump:h}

if [[ -n ${zdump}(#qN.mh+24) ]]; then
  compinit -d "$zdump"        # older than 24h: full rebuild + audit
else
  compinit -C -d "$zdump"     # fresh: trust cache, skip audit
fi

# Compile the dump so subsequent loads skip parsing.
if [[ -s $zdump && ( ! -s $zdump.zwc || $zdump -nt $zdump.zwc ) ]]; then
  zcompile -R "$zdump"
fi

unset zdump
