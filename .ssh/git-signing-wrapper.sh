#!/usr/bin/env sh

set -euo pipefail

LINK="$HOME/.ssh/id_secretive.pub"
KEY_DIR="$HOME/Library/Containers/com.maxgoedjen.Secretive.SecretAgent/Data/PublicKeys"
KEY_FILE="$(ls "$KEY_DIR" 2>/dev/null | head -n 1)"

if [ ! -d "$KEY_DIR" ] || [ -z "$KEY_FILE" ]; then
  echo "error: no Secretive key found in $KEY_DIR" >&2
  echo "Create a key in Secretive first." >&2
  exit 1
fi

# create symlink when it doesn't exist
if [ ! -e "$LINK" ]; then
  ln -sf "$KEY_DIR/$KEY_FILE" "$LINK"
fi

exec ssh-keygen -Y sign -f "$KEY_DIR/$KEY_FILE" "$@"
