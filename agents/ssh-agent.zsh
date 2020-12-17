if ! pgrep -u "$USER" ssh-agent > /dev/null; then
  eval $(ssh-agent -t 2h > /dev/null)
fi
