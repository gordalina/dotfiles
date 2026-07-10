# zmodload zsh/zprof

# XDG
export XDG_DATA_HOME=$HOME/.local/share
export XDG_CONFIG_HOME=$HOME/.config
export XDG_STATE_HOME=$HOME/.local/state
export XDG_CACHE_HOME=$HOME/.cache
export XDG_RUNTIME_DIR=/run/user/$UID

# Path to your Oh My Zsh installation.
export ZSH="$XDG_DATA_HOME/oh-my-zsh"
export ZSH_COMPDUMP="$ZSH_CACHE_DIR/.zcompdump"
export HIST_STAMPS="yyyy-mm-dd"

for file in ~/.config/zsh/zsh.d/*.zsh; do
  [ -f "$file" ] && source "$file"
done

# Compile zshrc
if [[ ! -f ~/.config/zsh/.zshrc.zwc || ~/.config/zsh/.zshrc -nt ~/.config/zsh/.zshrc.zwc ]]; then
  zcompile ~/.config/zsh/.zshrc
fi

# zprof