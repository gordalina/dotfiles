if ! pgrep -u "$USER" ssh-agent > /dev/null; then
  eval $(ssh-agent -t 2h > /dev/null)
  #ssh-add -A 2&>1 /dev/null
fi
