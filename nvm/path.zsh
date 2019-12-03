# nvm
export NVM_DIR="$HOME/.nvm"

nvm() {
  [ -s "$NVM_DIR/nvm.sh" ] && source "$NVM_DIR/nvm.sh"
  nvm $@
}
