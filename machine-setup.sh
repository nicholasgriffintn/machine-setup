#!/bin/bash

# This script will run a number of scripts to set up a user's machine for the first time

echo "To complete setup, you may be prompted for your password several times."
echo

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

sudo chsh -s /bin/zsh $USER

echo "Installing Antigen..."

mkdir -p "$HOME/.bin/antigen"

if [ ! -f "$HOME/.bin/antigen/antigen.zsh" ]; then
    curl -L git.io/antigen > $HOME/.bin/antigen/antigen.zsh
fi

sudo -v

if [[ $(command -v brew) == "" ]]; then
    echo "Installing Homebrew..."

    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
    eval "$(/opt/homebrew/bin/brew shellenv)"
else
    echo "Updating Homebrew"
    brew update
fi

echo "Installing brew dependencies..."

brew bundle --file=$SCRIPT_DIR/Brewfile

if [ "$SKIP_MAC_INSTALLS" != "true" ]; then
    echo "Installing mac store dependencies..."

    # Magnet
    mas install 441258766
    # YubiKey Personalization Tool
    mas install 638161122
    # Word
    mas install 462054704
    # Eccel
    mas install 462058435
    # PowerPoint
    mas install 462062816
    # Forklift
    mas install 412448059
    # Unsplash Wallpapers
    mas install 1284863847
    # Home Assistant
    mas install 1099568401
    # Runcat
    mas install 1429033973
    # Pandan
    mas install 1569600264
fi

if [ ! -d "~/workspace" ]; then
    echo "Setting up workspace..."

    mkdir -p ~/workspace
fi

cp $SCRIPT_DIR/zshrc-template ~/.zshrc

if [ ! -f "~/.nvm/nvm.sh" ]; then
    echo "Setting up NVM..."

    mkdir $HOME/.nvm

    export NVM_DIR="$HOME/.nvm"
    . "/opt/homebrew/opt/nvm/nvm.sh"

    nvm install --lts
fi

if [ ! -f "~/workspace/catppuccin_mocha-zsh-syntax-highlighting.zsh" ]; then
    echo "Copying zsh syntax highlighting theme..."

    cp $SCRIPT_DIR/catppuccin_mocha-zsh-syntax-highlighting.zsh ~/workspace/catppuccin_mocha-zsh-syntax-highlighting.zsh
fi

if [ ! -d "~/.cargo" ]; then
    echo "Installing Rust..."
    curl https://sh.rustup.rs -sSf | sh
fi

echo "Complete!"

sudo -k
