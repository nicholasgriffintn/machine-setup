#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

sudo chsh -s /bin/zsh $USER

echo "Configuring Machine..."

. ./machine-setup.sh

echo "Configuring Git..."

. ./git-setup.sh