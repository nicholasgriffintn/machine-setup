#!/bin/bash

set -euo pipefail

LOG_FILE="$HOME/machine-setup.log"

UPDATE_MODE="${UPDATE_MODE:-false}"
if [ "$UPDATE_MODE" != "true" ] && [ -z "${LOGGING_ENABLED:-}" ] && [ -f "$HOME/.zshrc" ] && grep -q "oh-my-posh" "$HOME/.zshrc" 2>/dev/null; then
    echo "Existing setup detected!"
    echo "This appears to be a machine that has already been set up."
    echo ""
    read -p "Do you want to run in UPDATE mode (safe, won't overwrite configs)? (Y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        UPDATE_MODE="true"
        export SKIP_BACKUP="true"
        echo "Running in UPDATE mode - will update packages but preserve configs"
    else
        echo "Continuing with FULL setup mode..."
    fi
    echo
fi

if [ -z "${LOGGING_ENABLED:-}" ]; then
    export LOGGING_ENABLED=1
    export UPDATE_MODE
    export SKIP_BACKUP="${SKIP_BACKUP:-false}"
    bash "$0" "$@" 2>&1 | tee -a "$LOG_FILE"
    exit "${PIPESTATUS[0]}"
fi

echo "=== Machine Setup Started: $(date) ==="
echo "Mode: $([ "$UPDATE_MODE" == "true" ] && echo "UPDATE" || echo "FULL SETUP")"
echo "Log file: $LOG_FILE"
echo

echo "To complete setup, you may be prompted for your password several times."
echo

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

sudo chsh -s /bin/zsh "$USER"

echo "Installing Antigen..."

mkdir -p "$HOME/.bin/antigen"

if [ ! -f "$HOME/.bin/antigen/antigen.zsh" ]; then
    echo "Downloading Antigen from GitHub..."
    curl -fsSL https://raw.githubusercontent.com/zsh-users/antigen/master/bin/antigen.zsh > "$HOME/.bin/antigen/antigen.zsh"
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

brew bundle --file="$SCRIPT_DIR/Brewfile" --verbose

if [ "${SKIP_MAC_INSTALLS:-false}" != "true" ]; then
    echo "Installing Mac App Store applications..."

    # Get list of already installed apps
    INSTALLED_APPS=$(mas list | awk '{print $1}')

    install_mas_app() {
        local app_id=$1
        local app_name=$2

        if echo "$INSTALLED_APPS" | grep -q "^$app_id$"; then
            echo "  ✓ $app_name already installed"
        else
            echo "  → Installing $app_name..."
            mas install "$app_id"
        fi
    }

    install_mas_app 441258766 "Magnet"
    install_mas_app 638161122 "YubiKey Personalization Tool"
    install_mas_app 462054704 "Microsoft Word"
    install_mas_app 462058435 "Microsoft Excel"
    install_mas_app 462062816 "Microsoft PowerPoint"
    install_mas_app 412448059 "Forklift"
    install_mas_app 1284863847 "Unsplash Wallpapers"
    install_mas_app 1099568401 "Home Assistant"
    install_mas_app 1429033973 "Runcat"
    install_mas_app 1569600264 "Pandan"
fi

if [ ! -d "$HOME/workspace" ]; then
    echo "Setting up workspace..."

    mkdir -p "$HOME/workspace"
fi

if [ "$UPDATE_MODE" != "true" ]; then
    if [ -f "$HOME/.zshrc" ] && [ "${SKIP_BACKUP:-false}" != "true" ]; then
        BACKUP_FILE="$HOME/.zshrc.backup.$(date +%s)"
        echo "Backing up existing .zshrc to $BACKUP_FILE"
        cp "$HOME/.zshrc" "$BACKUP_FILE"
    fi

    cp "$SCRIPT_DIR/zshrc-template" "$HOME/.zshrc"
else
    echo "Skipping .zshrc update (UPDATE_MODE enabled)"
fi

if [ ! -f "$HOME/.nvm/nvm.sh" ]; then
    echo "Setting up NVM..."

    mkdir -p "$HOME/.nvm"

    export NVM_DIR="$HOME/.nvm"
    . "/opt/homebrew/opt/nvm/nvm.sh"

    nvm install --lts
fi

if [ ! -f "$HOME/workspace/catppuccin_mocha-zsh-syntax-highlighting.zsh" ]; then
    echo "Copying zsh syntax highlighting theme..."

    cp "$SCRIPT_DIR/catppuccin_mocha-zsh-syntax-highlighting.zsh" "$HOME/workspace/catppuccin_mocha-zsh-syntax-highlighting.zsh"
fi

if [ ! -d "$HOME/.cargo" ]; then
    echo "Installing Rust..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable

    . "$HOME/.cargo/env"
fi

echo ""
echo "=== Verifying Installation ==="
echo ""

verify_command() {
    local cmd=$1
    local name=$2
    if command -v "$cmd" &> /dev/null; then
        local version=$($cmd --version 2>&1 | head -n 1)
        echo "✓ $name: $version"
        return 0
    else
        echo "✗ $name: NOT FOUND"
        return 1
    fi
}

verify_command "brew" "Homebrew"
verify_command "git" "Git"
verify_command "node" "Node.js"
verify_command "python3" "Python"
verify_command "go" "Go"
verify_command "rustc" "Rust"
verify_command "docker" "Docker"
verify_command "gh" "GitHub CLI"
verify_command "aws" "AWS CLI"

echo ""
echo "=== Setup Complete! ==="
echo "Log file saved to: $LOG_FILE"
echo "Please restart your terminal or run: source ~/.zshrc"
echo ""

sudo -k
