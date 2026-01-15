#!/bin/bash

set -euo pipefail

LOG_FILE="$HOME/machine-setup.log"
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Logging wrapper - re-exec with script if not already logging
if [ -z "${MACHINE_SETUP_LOGGING:-}" ]; then
    export MACHINE_SETUP_LOGGING=1
    script -q "$LOG_FILE" bash "$0" "$@"
    exit $?
fi

# Keep sudo alive in the background
while true; do sudo -n true; sleep 60; kill -0 "$$" || exit; done 2>/dev/null &

# Detect update mode
UPDATE_MODE=false
if [ -f "$HOME/.zshrc" ] && grep -q "oh-my-posh" "$HOME/.zshrc" 2>/dev/null; then
    if command -v gum &> /dev/null; then
        gum style --border rounded --padding "1 2" --margin "1" \
            "Existing setup detected!" \
            "This appears to be a machine that has already been set up."
        
        if gum confirm "Run in UPDATE mode? (won't overwrite configs)"; then
            UPDATE_MODE=true
            gum style --foreground 2 "✓ Running in UPDATE mode"
        else
            gum style --foreground 3 "⚠ Running in FULL setup mode"
        fi
    else
        echo "Existing setup detected!"
        echo "This appears to be a machine that has already been set up."
        echo ""
        read -p "Do you want to run in UPDATE mode (safe, won't overwrite configs)? (Y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            UPDATE_MODE=true
            echo "✓ Running in UPDATE mode"
        else
            echo "⚠ Running in FULL setup mode"
        fi
    fi
    echo
fi

if command -v gum &> /dev/null; then
    gum style --border double --padding "1 2" --margin "1" --foreground 212 \
        "Machine Setup Started: $(date)" \
        "Mode: $([ "$UPDATE_MODE" = true ] && echo "UPDATE" || echo "FULL SETUP")" \
        "Log: $LOG_FILE"
else
    echo "=== Machine Setup Started: $(date) ==="
    echo "Mode: $([ "$UPDATE_MODE" = true ] && echo "UPDATE" || echo "FULL SETUP")"
    echo "Log file: $LOG_FILE"
fi
echo

# Change shell to zsh if not already set
if [ "$SHELL" != "/bin/zsh" ]; then
    if command -v gum &> /dev/null; then
        gum style --foreground 212 "Changing default shell to zsh..."
    else
        echo "Changing default shell to zsh..."
    fi
    sudo chsh -s /bin/zsh "$USER"
else
    if command -v gum &> /dev/null; then
        gum style --foreground 2 "✓ Shell is already set to zsh"
    else
        echo "✓ Shell is already set to zsh"
    fi
fi
sudo -v

# Install/Update Homebrew
if [[ $(command -v brew) == "" ]]; then
    if command -v gum &> /dev/null; then
        gum spin --spinner dot --title "Installing Homebrew..." -- \
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    else
        echo "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    # Add brew shellenv to .zprofile if not already present
    if [ -f ~/.zprofile ] && grep -q 'brew shellenv' ~/.zprofile; then
        if command -v gum &> /dev/null; then
            gum style --foreground 2 "✓ Homebrew shellenv already in .zprofile"
        fi
    else
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
        if command -v gum &> /dev/null; then
            gum style --foreground 2 "✓ Added Homebrew shellenv to .zprofile"
        fi
    fi
    eval "$(/opt/homebrew/bin/brew shellenv)"
else
    if command -v gum &> /dev/null; then
        gum spin --spinner dot --title "Updating Homebrew..." -- brew update
    else
        echo "Updating Homebrew"
        brew update
    fi
fi

# Install brew dependencies
if command -v gum &> /dev/null; then
    gum style --foreground 212 "Installing brew dependencies..."
    brew bundle --file="$SCRIPT_DIR/Brewfile" --verbose
else
    echo "Installing brew dependencies..."
    brew bundle --file="$SCRIPT_DIR/Brewfile" --verbose
fi

# Configure git-delta
if command -v delta &> /dev/null; then
    if command -v gum &> /dev/null; then
        gum style --foreground 2 "✓ Configuring git-delta..."
    else
        echo "Configuring git-delta..."
    fi
    git config --global core.pager "delta"
    git config --global interactive.diffFilter "delta --color-only"
    git config --global delta.navigate true
    git config --global delta.light false
    git config --global merge.conflictstyle "diff3"
    git config --global diff.colorMoved "default"
fi

# Mac App Store installations
# Using parallel arrays for bash 3.2 compatibility
MAS_APP_IDS=(
    "441258766"
    "638161122"
    "462054704"
    "462058435"
    "462062816"
    "412448059"
    "1284863847"
    "1099568401"
    "1429033973"
    "1569600264"
)

MAS_APP_NAMES=(
    "Magnet"
    "YubiKey Personalization Tool"
    "Microsoft Word"
    "Microsoft Excel"
    "Microsoft PowerPoint"
    "Forklift"
    "Unsplash Wallpapers"
    "Home Assistant"
    "Runcat"
    "Pandan"
)

if command -v gum &> /dev/null; then
    gum style --foreground 212 "Select Mac App Store applications to install:"
    
    # Sort app names for display
    SORTED_NAMES=($(printf '%s\n' "${MAS_APP_NAMES[@]}" | sort))
    
    # Let user select apps (multi-select with --no-limit)
    SELECTED_APPS=$(printf '%s\n' "${SORTED_NAMES[@]}" | gum choose --no-limit --header "Use space to select, enter to confirm")
    
    if [ -n "$SELECTED_APPS" ]; then
        INSTALLED_APPS=$(mas list | awk '{print $1}')
        
        install_mas_app() {
            local app_id=$1
            local app_name=$2
            
            if echo "$INSTALLED_APPS" | grep -q "^$app_id$"; then
                gum style --foreground 2 "  ✓ $app_name already installed"
            else
                gum spin --spinner dot --title "  Installing $app_name..." -- mas install "$app_id"
            fi
        }
        
        # Install selected apps
        while IFS= read -r app_name; do
            # Find the index of the app name
            for i in "${!MAS_APP_NAMES[@]}"; do
                if [ "${MAS_APP_NAMES[$i]}" = "$app_name" ]; then
                    install_mas_app "${MAS_APP_IDS[$i]}" "$app_name"
                    break
                fi
            done
        done <<< "$SELECTED_APPS"
    else
        gum style --foreground 3 "No apps selected, skipping Mac App Store installations"
    fi
else
    # Fallback for non-gum installation
    echo "Installing Mac App Store applications..."
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

# Setup workspace
if command -v gum &> /dev/null; then
    DEFAULT_WORKSPACE="$HOME/workspace"
    WORKSPACE_DIR=$(gum input --placeholder "$DEFAULT_WORKSPACE" --prompt "Workspace directory: " --value "$DEFAULT_WORKSPACE")
    if [ -z "$WORKSPACE_DIR" ]; then
        WORKSPACE_DIR="$DEFAULT_WORKSPACE"
    fi
else
    WORKSPACE_DIR="$HOME/workspace"
fi

if [ ! -d "$WORKSPACE_DIR" ]; then
    mkdir -p "$WORKSPACE_DIR"
    if command -v gum &> /dev/null; then
        gum style --foreground 2 "✓ Created workspace directory: $WORKSPACE_DIR"
    else
        echo "Created workspace directory: $WORKSPACE_DIR"
    fi
fi

# Config Setup
if [ "$UPDATE_MODE" != true ]; then
    if [ -f "$HOME/.zshrc" ]; then
        BACKUP_FILE="$HOME/.zshrc.backup.$(date +%s)"
        if command -v gum &> /dev/null; then
            gum style --foreground 3 "Backing up existing .zshrc to $BACKUP_FILE"
        else
            echo "Backing up existing .zshrc to $BACKUP_FILE"
        fi
        cp "$HOME/.zshrc" "$BACKUP_FILE"
    fi

    if command -v gum &> /dev/null; then
        gum style --foreground 212 "Installing Zsh configuration..."
    else
        echo "Installing Zsh configuration..."
    fi
    cp "$SCRIPT_DIR/zshrc-template" "$HOME/.zshrc"
    
    mkdir -p "$HOME/.config/zsh"
    cp "$SCRIPT_DIR/zsh/"*.zsh "$HOME/.config/zsh/"
    cp "$SCRIPT_DIR/zsh_plugins.txt" "$HOME/.zsh_plugins.txt"
else
    if command -v gum &> /dev/null; then
        gum style --foreground 3 "Skipping .zshrc update (UPDATE_MODE)"
        gum style --foreground 212 "Updating Zsh partials..."
    else
        echo "Skipping .zshrc update (UPDATE_MODE enabled)"
        echo "Updating Zsh partials..."
    fi
    mkdir -p "$HOME/.config/zsh"
    cp "$SCRIPT_DIR/zsh/"*.zsh "$HOME/.config/zsh/"
    cp "$SCRIPT_DIR/zsh_plugins.txt" "$HOME/.zsh_plugins.txt"
fi

# Copy theme and configs
if [ ! -f "$WORKSPACE_DIR/catppuccin_mocha-zsh-syntax-highlighting.zsh" ]; then
    cp "$SCRIPT_DIR/catppuccin_mocha-zsh-syntax-highlighting.zsh" "$WORKSPACE_DIR/catppuccin_mocha-zsh-syntax-highlighting.zsh"
fi

if [ -f "$SCRIPT_DIR/fastfetch-config.jsonc" ]; then
    if [ ! -f "$WORKSPACE_DIR/fastfetch-config.jsonc" ]; then
        cp "$SCRIPT_DIR/fastfetch-config.jsonc" "$WORKSPACE_DIR/fastfetch-config.jsonc"
    fi
fi

if [ -f "$SCRIPT_DIR/fastfetch-logo.txt" ]; then
    if [ ! -f "$WORKSPACE_DIR/fastfetch-logo.txt" ]; then
        cp "$SCRIPT_DIR/fastfetch-logo.txt" "$WORKSPACE_DIR/fastfetch-logo.txt"
    fi
fi

# Install Rust
if [ ! -d "$HOME/.cargo" ]; then
    if command -v gum &> /dev/null; then
        gum spin --spinner dot --title "Installing Rust..." -- \
            bash -c 'curl --proto "=https" --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable'
    else
        echo "Installing Rust..."
        curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
    fi
    . "$HOME/.cargo/env"
fi

# Run macOS defaults
if [ "$UPDATE_MODE" != true ]; then
    if command -v gum &> /dev/null; then
        if gum confirm "Apply macOS defaults (Finder, Dock, keyboard settings)?"; then
            gum spin --spinner dot --title "Applying macOS defaults..." -- \
                bash "$SCRIPT_DIR/macos-defaults.sh"
        fi
    else
        echo "Applying macOS defaults..."
        bash "$SCRIPT_DIR/macos-defaults.sh"
    fi
fi

# Verification
echo ""
if command -v gum &> /dev/null; then
    gum style --border rounded --padding "1 2" --foreground 212 "Verifying Installation"
else
    echo "=== Verifying Installation ==="
fi
echo ""

# Collect verification data
VERIFICATION_DATA=()

verify_command() {
    local cmd=$1
    local name=$2
    local version=""
    
    if command -v "$cmd" &> /dev/null; then
        # Try different version flag formats
        case "$cmd" in
            go)
                version=$(go version 2>&1 | head -n 1)
                ;;
            melt)
                version=$(melt version 2>&1 | head -n 1 || echo "installed")
                ;;
            soft)
                version=$(soft version 2>&1 | head -n 1 || echo "installed")
                ;;
            *)
                version=$($cmd --version 2>&1 | head -n 1)
                # If --version failed, try -version
                if [[ $version == *"unknown"* ]] || [[ $version == *"illegal"* ]] || [[ $version == *"Error"* ]]; then
                    version=$($cmd -version 2>&1 | head -n 1 || echo "installed")
                fi
                ;;
        esac
        
        # Clean up error messages
        if [[ $version == *"Error"* ]] || [[ $version == *"unknown"* ]] || [[ $version == *"illegal"* ]]; then
            version="installed"
        fi
        
        if command -v gum &> /dev/null; then
            VERIFICATION_DATA+=("$name|✓|$version")
        else
            echo "✓ $name: $version"
        fi
        return 0
    else
        if command -v gum &> /dev/null; then
            VERIFICATION_DATA+=("$name|✗|NOT FOUND")
        else
            echo "✗ $name: NOT FOUND"
        fi
        return 1
    fi
}

verify_command "brew" "Homebrew"
verify_command "git" "Git"
verify_command "fnm" "FNM (Node Manager)"
verify_command "python3" "Python"
verify_command "go" "Go"
verify_command "rustc" "Rust"
verify_command "docker" "Docker"
verify_command "gh" "GitHub CLI"
verify_command "aws" "AWS CLI"
verify_command "gum" "Gum"
verify_command "soft" "Soft Serve"
verify_command "skate" "Skate"
verify_command "melt" "Melt"

# Display results in table format if gum is available
if command -v gum &> /dev/null && [ ${#VERIFICATION_DATA[@]} -gt 0 ]; then
    {
        echo "Tool,Status,Version"
        for row in "${VERIFICATION_DATA[@]}"; do
            # Split on pipe and properly quote each field
            IFS='|' read -r tool status version <<< "$row"
            # Clean version string: remove commas and quotes, truncate if too long
            version=$(echo "$version" | tr -d ',' | tr -d '"' | cut -c 1-50)
            # Output as CSV with quoted fields
            echo "\"$tool\",\"$status\",\"$version\""
        done
    } | gum table --separator ","
else
    # If gum table fails or isn't available, fall back to simple output
    if [ ${#VERIFICATION_DATA[@]} -gt 0 ]; then
        for row in "${VERIFICATION_DATA[@]}"; do
            IFS='|' read -r tool status version <<< "$row"
            if [ "$status" = "✓" ]; then
                echo "✓ $tool: $version"
            else
                echo "✗ $tool: $version"
            fi
        done
    fi
fi

echo ""
if command -v gum &> /dev/null; then
    gum format -- "# 🎉 Setup Complete!" \
        "" \
        "Your machine has been successfully configured!" \
        "" \
        "## 📋 Summary" \
        "- **Mode**: $([ "$UPDATE_MODE" = true ] && echo "UPDATE" || echo "FULL SETUP")" \
        "- **Workspace**: \`$WORKSPACE_DIR\`" \
        "- **Log File**: \`$LOG_FILE\`" \
        "" \
        "## 🚀 Next Steps" \
        "1. Restart your terminal or run: \`source ~/.zshrc\`" \
        "2. Verify your setup with: \`which fnm\` and other tools" \
        "3. Customize your \`.zshrc\` as needed" \
        "" \
        "## 💡 Useful Commands" \
        "- \`brew update && brew upgrade\` - Update packages" \
        "- \`gh auth login\` - Authenticate with GitHub"
else
    echo "=== Setup Complete! ==="
    echo "Log file saved to: $LOG_FILE"
    echo "Workspace: $WORKSPACE_DIR"
    echo "Please restart your terminal or run: source ~/.zshrc"
fi
echo ""

sudo -k
