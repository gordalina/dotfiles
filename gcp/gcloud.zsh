$GCLOUD_PATH="$(brew --prefix)/Caskroom/google-cloud-sdk/latest/google-cloud-sdk"

# The next line updates PATH for the Google Cloud SDK.
if [ -f "$GCLOUD_PATH/path.zsh.inc" ]; then . '/usr/local/opt/google-cloud-sdk/path.zsh.inc'; fi

# The next line enables shell command completion for gcloud.
if [ -f "$GCLOUD_PATH/completion.zsh.inc" ]; then . '/usr/local/opt/google-cloud-sdk/completion.zsh.inc'; fi
