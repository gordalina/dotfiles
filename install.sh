#!/usr/bin/env sh

echo "› install homebrew"
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

echo "› cloning dotfiles"
mkdir -p ~/src
git clone git@github.com:gordalina/dotfiles.git ~/src/dotfiles

echo "› bootstrap dotfiles"
brew install mise
(cd ~/src/dotfiles; mise bootstrap)

echo "› applying defaults"
sudo ~/src/dotfiles/bin/dot

echo "› install oh-my-zsh"
ZSH=~/.local/share/oh-my-zsh RUNZSH=no KEEP_ZSHRC=YES sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"

echo "› brew install"
brew bundle

echo "› all done!"

exec zsh