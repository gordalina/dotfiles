# zmodload zsh/zprof

# XDG
export XDG_DATA_HOME=$HOME/.local/share
export XDG_CONFIG_HOME=$HOME/.config
export XDG_STATE_HOME=$HOME/.local/state
export XDG_CACHE_HOME=$HOME/.cache
export XDG_RUNTIME_DIR=/run/user/$UID

# Autload
for file in ~/.config/zsh/zsh.d/*.zsh; do
  [ -f "$file" ] && source "$file"
done

# Compile zshrc
if [[ ! -f ~/.config/zsh/.zshrc.zwc || ~/.config/zsh/.zshrc -nt ~/.config/zsh/.zshrc.zwc ]]; then
  zcompile ~/.config/zsh/.zshrc
fi

# zprof