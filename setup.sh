#!/bin/bash

set -euo pipefail

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Change shell to zsh if not already set
if [ "$SHELL" != "/bin/zsh" ]; then
    sudo chsh -s /bin/zsh "$USER"
fi

echo "Configuring Machine..."

. "$SCRIPT_DIR/machine-setup.sh"

if command -v gum &> /dev/null; then
    if gum confirm "Configure Git and GPG signing?"; then
        echo "Configuring Git..."
        . "$SCRIPT_DIR/git-setup.sh"
    fi
else
    read -p "Configure Git and GPG signing? (Y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Configuring Git..."
        . "$SCRIPT_DIR/git-setup.sh"
    fi
fi
