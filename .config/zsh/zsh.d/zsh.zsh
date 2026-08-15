export SHELL_SESSION_DIR="${XDG_STATE_HOME}/zsh/sessions"
export HISTFILE="${XDG_STATE_HOME}/zsh/history"

mkdir -p "${SHELL_SESSION_DIR}" "${HISTFILE:h}"