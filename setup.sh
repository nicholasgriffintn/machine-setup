#!/bin/bash

set -euo pipefail

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
source "$SCRIPT_DIR/lib/gum-utils.sh"

if [ "$SHELL" != "/bin/zsh" ]; then
    sudo chsh -s /bin/zsh "$USER"
fi

log info "Configuring Machine..."

. "$SCRIPT_DIR/machine-setup.sh"

if confirm "Configure Git and GPG signing?"; then
    log info "Configuring Git..."
    . "$SCRIPT_DIR/git-setup.sh"
fi
