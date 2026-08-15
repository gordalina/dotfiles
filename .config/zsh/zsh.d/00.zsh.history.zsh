export SHELL_SESSION_DIR="${XDG_STATE_HOME}/zsh/sessions"
export HISTFILE="${XDG_STATE_HOME}/zsh/history"
export HISTSIZE=100000
export SAVEHIST=100000

# Record the timestamp and the duration of each command
setopt EXTENDED_HISTORY

# Write each command to the file at once, and read new commands from
# other shells before each prompt. Keep INC_APPEND_HISTORY off with this.
setopt SHARE_HISTORY

# Drop an older copy of a command when you run it again
setopt HIST_IGNORE_ALL_DUPS

# Drop duplicates when the history file is written
setopt HIST_SAVE_NO_DUPS

# Do not record a command that starts with a space
setopt HIST_IGNORE_SPACE

# Remove extra blanks from a command before it is recorded
setopt HIST_REDUCE_BLANKS

# Expand "!!" onto the command line instead of running it at once
setopt HIST_VERIFY

mkdir -p "${SHELL_SESSION_DIR}" "${HISTFILE:h}"