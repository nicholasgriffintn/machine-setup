#!/bin/bash

set -euo pipefail

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
source "$SCRIPT_DIR/lib/gum-utils.sh"

echo "To complete setup, you may be prompted for your MacOS password several times."
echo

log info "Adding global git configs..."

git config --global push.default current
git config --global fetch.prune true
git config --global pull.rebase true
git config --global diff.colorMoved zebra
echo

GIT_NAME=$(git config --get user.name || echo "")
GIT_EMAIL=$(git config --get user.email || echo "")

if [ -z "$GIT_NAME" ] || [ -z "$GIT_EMAIL" ]; then
    log error "Git user.name and user.email are not configured!"
    log plain "Please run the following commands first:"
    log warn "  git config --global user.name \"Your Name\""
    log warn "  git config --global user.email \"your.email@example.com\""
    exit 1
fi

log_banner rounded \
    "Please verify your Git configuration:" \
    "" \
    "Name: $GIT_NAME" \
    "Email: $GIT_EMAIL"

if ! confirm "Are these correct?"; then
    log warn "Please update your Git config and run this script again:"
    log warn "  git config --global user.name \"Your Name\""
    log warn "  git config --global user.email \"your.email@example.com\""
    exit 1
fi
echo

spin "Installing gpg-suite..." brew install --cask gpg-suite
echo

EXISTING_KEY=$(gpg --list-secret-keys --with-colons "$GIT_EMAIL" 2>/dev/null | grep "^sec:u:" | cut -f5 -d":" | head -n 1)

if [ -n "$EXISTING_KEY" ]; then
    log success "GPG key already exists for $GIT_EMAIL"
    signingkey="$EXISTING_KEY"
else
    spin "Generating GPG key..." bash -c "
        gpg --batch --generate-key - <<-EOS
             Key-Type: RSA
             Key-Length: 4096
             Name-Real: $GIT_NAME
             Name-Email: $GIT_EMAIL
             Expire-Date: 0
             %commit
EOS
    "
    signingkey=$(gpg --list-secret-keys --fixed-list-mode --with-colons | grep "^sec:u:" | cut -f5 -d":" | tail -n 1)
fi
echo

log success "Configuring git to sign commits..."

git config --global commit.gpgsign true
git config --global user.signingkey "$signingkey"
git config --global --unset gpg.x509.program || true
git config --global --unset gpg.format || true
echo

log_banner rounded \
    "Final Step: Add GPG Key to GitHub" \
    "" \
    "We will open GitHub in your browser." \
    "Your GPG key is already copied to clipboard." \
    "" \
    "1. Click 'New GPG key'" \
    "2. Paste from clipboard (Cmd+V)" \
    "3. Save"

confirm "Ready to open browser?" || exit 0

gpg --armor --export "$(git config --global --get user.signingkey)" | pbcopy
open "https://github.com/settings/gpg/new"