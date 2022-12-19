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

echo "Installing Homebrew..."

if [ ! -f /usr/local/bin/brew ]; then
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
    eval "$(/opt/homebrew/bin/brew shellenv)"
fi


echo "Installing brew dependencies..."

brew bundle --file=$SCRIPT_DIR/Brewfile

if [ ! -f "~/workspace" ]; then
    echo "Setting up workspace..."

    mkdir -p ~/workspace
fi

cp $SCRIPT_DIR/zshrc-template ~/.zshrc

if [ ! -f "~/.nvm" ]; then
    echo "Setting up NVM..."

    mkdir $HOME/.nvm

    export NVM_DIR="$HOME/.nvm"
    . "/opt/homebrew/opt/nvm/nvm.sh"

    nvm install --lts
fi

echo "Complete!"

sudo -k