#!/bin/bash

set -euo pipefail

echo "To complete setup, you may be prompted for your MacOS password several times."
echo

if command -v gum &> /dev/null; then
    gum style --foreground 212 "Adding global git configs..."
else
    echo "Adding global git configs..."
fi

git config --global push.default current
git config --global fetch.prune true
git config --global pull.rebase true
git config --global diff.colorMoved zebra
echo

GIT_NAME=$(git config --get user.name || echo "")
GIT_EMAIL=$(git config --get user.email || echo "")

if [ -z "$GIT_NAME" ] || [ -z "$GIT_EMAIL" ]; then
    if command -v gum &> /dev/null; then
        gum style --foreground 1 --bold "ERROR: Git user.name and user.email are not configured!"
        gum style "Please run the following commands first:"
        gum style --foreground 3 "  git config --global user.name \"Your Name\""
        gum style --foreground 3 "  git config --global user.email \"your.email@example.com\""
    else
        echo "ERROR: Git user.name and user.email are not configured!"
        echo "Please run the following commands first:"
        echo "  git config --global user.name \"Your Name\""
        echo "  git config --global user.email \"your.email@example.com\""
    fi
    exit 1
fi

if command -v gum &> /dev/null; then
    gum style --border rounded --padding "1 2" \
        "Please verify your Git configuration:" \
        "" \
        "Name: $GIT_NAME" \
        "Email: $GIT_EMAIL"
    
    if ! gum confirm "Are these correct?"; then
        gum style --foreground 3 "Please update your Git config and run this script again:"
        gum style --foreground 3 "  git config --global user.name \"Your Name\""
        gum style --foreground 3 "  git config --global user.email \"your.email@example.com\""
        exit 1
    fi
else
    echo "Please check if your configured git Name and Email are correct and the same as used on GitHub:"
    echo
    echo "Name: $GIT_NAME"
    echo "Email: $GIT_EMAIL"
    echo
    
    read -p "Are these correct? (Y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Please setup your GitHub username and email and then run this script again."
        echo "  git config --global user.name \"Your Name\""
        echo "  git config --global user.email \"your.email@example.com\""
        exit 1
    fi
fi
echo

if command -v gum &> /dev/null; then
    gum spin --spinner dot --title "Installing gpg-suite..." -- \
        brew install --cask gpg-suite
else
    echo "Installing gpg-suite..."
    HOMEBREW_NO_AUTO_UPDATE=1 brew install --cask gpg-suite
fi
echo

# Check if a GPG key already exists for this email
EXISTING_KEY=$(gpg --list-secret-keys --with-colons "$GIT_EMAIL" 2>/dev/null | grep "^sec:u:" | cut -f5 -d":" | head -n 1)

if [ -n "$EXISTING_KEY" ]; then
    if command -v gum &> /dev/null; then
        gum style --foreground 2 "✓ GPG key already exists for $GIT_EMAIL"
    else
        echo "✓ GPG key already exists for $GIT_EMAIL"
    fi
    signingkey="$EXISTING_KEY"
else
    if command -v gum &> /dev/null; then
        gum spin --spinner dot --title "Generating GPG key..." -- bash -c "
            gpg --batch --generate-key - <<-EOS
                 Key-Type: RSA
                 Key-Length: 4096
                 Name-Real: $GIT_NAME
                 Name-Email: $GIT_EMAIL
                 Expire-Date: 0
                 %commit
EOS
        "
    else
        echo "Generating GPG key..."
        gpg --batch --generate-key - <<-EOS
             Key-Type: RSA
             Key-Length: 4096
             Name-Real: $GIT_NAME
             Name-Email: $GIT_EMAIL
             Expire-Date: 0
             %commit
EOS
    fi
    signingkey=$(gpg --list-secret-keys --fixed-list-mode --with-colons | grep "^sec:u:" | cut -f5 -d":" | tail -n 1)
fi
echo

if command -v gum &> /dev/null; then
    gum style --foreground 2 "✓ Configuring git to sign commits..."
else
    echo "Configuring git to sign commits..."
fi

git config --global commit.gpgsign true
git config --global user.signingkey "$signingkey"
git config --global --unset gpg.x509.program || true
git config --global --unset gpg.format || true
echo

if command -v gum &> /dev/null; then
    gum style --border rounded --padding "1 2" --foreground 212 \
        "Final Step: Add GPG Key to GitHub" \
        "" \
        "We will open GitHub in your browser." \
        "Your GPG key is already copied to clipboard." \
        "" \
        "1. Click 'New GPG key'" \
        "2. Paste from clipboard (Cmd+V)" \
        "3. Save"
    
    gum confirm "Ready to open browser?" || exit 0
else
    echo "As last step you will have to add your new key to GitHub."
    echo
    echo "We will now open a browser window, where you can add this key. (https://github.com/settings/gpg/new)"
    echo "Once logged in to GitHub, choose \"New GPG key\" and paste the contents from your clipboard. Then save."
    echo
    
    read -p "Press any key to continue in browser... " -n 1 -r
    echo
fi

gpg --armor --export "$(git config --global --get user.signingkey)" | pbcopy
open "https://github.com/settings/gpg/new"