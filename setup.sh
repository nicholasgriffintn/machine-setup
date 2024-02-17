#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

sudo chsh -s /bin/zsh $USER

echo "Configuring Machine..."

. ./machine-setup.sh

if [ "$CONFIGURE_GIT" == "true" ]; then
    echo "Configuring Git..."

    . ./git-setup.sh
fi
