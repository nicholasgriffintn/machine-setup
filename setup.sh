#!/bin/bash

set -euo pipefail

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

sudo chsh -s /bin/zsh "$USER"

echo "Configuring Machine..."

. "$SCRIPT_DIR/machine-setup.sh"

if [ "${CONFIGURE_GIT:-false}" == "true" ]; then
    echo "Configuring Git..."

    . "$SCRIPT_DIR/git-setup.sh"
fi
