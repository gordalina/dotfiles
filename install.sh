#!/usr/bin/env sh

set -euxo pipefail

echo "› set computer name"
printf "  computer name [sg]: "
read -r name < /dev/tty
name="${name:-sg}"
sudo scutil --set ComputerName "$name"
sudo scutil --set HostName "$name"
sudo scutil --set LocalHostName "$name"
sudo defaults write /Library/Preferences/SystemConfiguration/com.apple.smb.server NetBIOSName -string "$name"

echo "› install developer tools"
sudo xcode-select --install

echo "› install homebrew"
NOINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
eval "$(/opt/homebrew/bin/brew shellenv zsh)"

echo "› cloning dotfiles"
mkdir -p ~/src
git clone https://github.com/gordalina/dotfiles ~/src/dotfiles
cd ~/src/dotfiles

echo "› bootstrap dotfiles"
curl https://mise.run | sh
mise bootstrap
mise bootstrap:once

echo "› all done!"

exec zsh