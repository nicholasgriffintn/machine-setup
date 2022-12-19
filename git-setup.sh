#!/bin/bash

# This script will run a number of scripts to set up a user's git for the first time

echo "To complete setup, you may be prompted for your MacOS password several times."
echo 

echo "Adding global git configs..."
git config --global push.default current
git config --global fetch.prune true
git config --global pull.rebase true
git config --global diff.colorMoved zebra
echo

echo "Please check if your configured git Name and Email are correct and the same as used on GitHub:"
echo
echo "Name: `git config --get user.name`"
echo "Email: `git config --get user.email`"
echo

read -p "Are these correct? (Y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "Please setup you GitHub username and email and then run this script again."
    [[ "$0" = "$BASH_SOURCE" ]] && exit 1 || return 1
fi
echo

echo "Installing gpg-suite..."
HOMEBREW_NO_AUTO_UPDATE=1 brew install --cask gpg-suite
echo

echo "Generating GPG key..."
gpg --batch --generate-key - <<-EOS
     Key-Type: RSA
     Key-Length: 4096
     Name-Real: `git config --get user.name`
     Name-Email: `git config --get user.email`
     Expire-Date: 0
     %commit
EOS
signingkey=$(gpg --list-secret-keys --fixed-list-mode --with-colons | grep "^sec:u:" | cut -f5 -d":" | tail -n 1)
echo

echo "Configuring git to sign commits..."
git config --global commit.gpgsign true
git config --global user.signingkey $signingkey
git config --global --unset gpg.x509.program
git config --global --unset gpg.format
echo

echo "As last step you will have to add your new key to GitHub."
echo
echo "We will now open a browser window, where you can add this key. (https://github.com/settings/gpg/new)"
echo "Once logged in to GitHub, choose \"New GPG key\" and paste the contents from your clipboard. Then save."
echo

read -p "Press any key to continue in browser... " -n 1 -r

gpg --armor --export `git config --global --get user.signingkey` | pbcopy
open "https://github.com/settings/gpg/new"