alias reload!='. ~/.zshrc'
alias cls='clear' # Good 'ol Clear Screen command

# pattern matching
alias s='sift --line-number --git --binary-skip'
alias se='sift --line-number --git --binary-skip --regexp'
alias si='sift --line-number --ignore-case --git --binary-skip'
alias sei='sift --line-number --ignore-case --git --binary-skip --regexp'
alias sf='find . | s'
alias sfi='find . | si'
alias sfe='find . | se'
alias sfei='find . | sei'
alias gv='grep -v'

# directory traversing
alias ..='cd ..'
alias ...='cd ../..'
