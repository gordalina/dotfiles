# If you come from bash you might have to change your $PATH.
# export PATH=$HOME/bin:$HOME/.local/bin:/usr/local/bin:$PATH

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

# Set name of the theme to load --- if set to "random", it will
# load a random theme each time Oh My Zsh is loaded, in which case,
# to know which specific one was loaded, run: echo $RANDOM_THEME
# See https://github.com/ohmyzsh/ohmyzsh/wiki/Themes
ZSH_THEME="robbyrussell"

plugins=(git)

source $ZSH/oh-my-zsh.sh

for file in ~/.config/zsh/zsh.d/*.zsh; do
  [ -f "$file" ] && source "$file"
done
