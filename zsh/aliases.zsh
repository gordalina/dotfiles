alias reload!='. ~/.zshrc'
alias cls='clear' # Good 'ol Clear Screen command

# pattern matching
alias s='sift --git --binary-skip'
alias se='sift --git --binary-skip --regexp'
alias si='sift --ignore-case --git --binary-skip'
alias sei='sift --ignore-case --git --binary-skip --regexp'
alias sf='find . | s'
alias sfi='find . | si'
alias sfe='find . | se'
alias sfei='find . | sei'
alias gv='grep -v'

# directory traversing
alias ..='cd ..'
alias ...='cd ../..'
