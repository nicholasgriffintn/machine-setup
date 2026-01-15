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

source "$SCRIPT_DIR/lib/gum-utils.sh"

# Detect update mode
UPDATE_MODE=false
if [ -f "$HOME/.zshrc" ] && grep -q "oh-my-posh" "$HOME/.zshrc" 2>/dev/null; then
    log_banner rounded "Existing setup detected!" "This appears to be a machine that has already been set up."

    if confirm "Run in UPDATE mode? (won't overwrite configs)"; then
        UPDATE_MODE=true
        log info "Running in UPDATE mode"
    else
        log info "Running in FULL setup mode"
    fi
    echo
fi

log_banner double \
    "Machine Setup Started: $(date)" \
    "Mode: $([ "$UPDATE_MODE" = true ] && echo "UPDATE" || echo "FULL SETUP")" \
    "Log: $LOG_FILE"
echo

OS=$(uname -s 2> /dev/null)
if [ "$OS" != "Darwin" ]; then
    log error "This setup script is intended for macOS systems only. Detected OS: $OS"
    exit 1
fi

if ! ping -c 1 nicholasgriffin.dev &> /dev/null; then
    log error "No internet connectivity detected. Please check your network and try again."
    exit 1
fi

if [ "$SHELL" != "/bin/zsh" ]; then
    log info "Changing default shell to zsh..."
    sudo chsh -s /bin/zsh "$USER"
else
    log success "Shell is already set to zsh"
fi
sudo -v

if [ ! -f "$HOME/.ssh/id_rsa.pub" ] && [ ! -f "$HOME/.ssh/id_ed25519.pub" ]; then
    log info "Generating a new SSH key..."
    EMAIL=$(input "Enter your email for the SSH key" "")
    ssh-keygen -t ed25519 -C "$EMAIL" -f "$HOME/.ssh/id_ed25519" -N ""
    log success "SSH key generated at ~/.ssh/id_ed25519"
else
    log success "SSH key already exists"
fi

if [[ $(command -v brew) == "" ]]; then
    spin "Installing Homebrew..." /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    if [ -f ~/.zprofile ] && grep -q 'brew shellenv' ~/.zprofile; then
        log success "Homebrew shellenv already in .zprofile"
    else
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
        log success "Added Homebrew shellenv to .zprofile"
    fi
    eval "$(/opt/homebrew/bin/brew shellenv)"
else
    spin "Updating Homebrew..." brew update
fi

log info "Installing brew dependencies..."
brew bundle --file="$SCRIPT_DIR/Brewfile" --verbose

if command -v delta &> /dev/null; then
    log success "Configuring git-delta..."
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

install_mas_app() {
    local app_id=$1
    local app_name=$2
    local installed_apps=$3

    if echo "$installed_apps" | grep -q "^$app_id$"; then
        log success "  $app_name already installed"
    else
        spin "  Installing $app_name..." mas install "$app_id"
    fi
}

INSTALLED_APPS=$(mas list | awk '{print $1}')

if $HAS_GUM; then
    log info "Select Mac App Store applications to install:"
    SORTED_NAMES=($(printf '%s\n' "${MAS_APP_NAMES[@]}" | sort))
    SELECTED_APPS=$(printf '%s\n' "${SORTED_NAMES[@]}" | gum choose --no-limit --header "Use space to select, enter to confirm")

    if [ -n "$SELECTED_APPS" ]; then
        while IFS= read -r app_name; do
            for i in "${!MAS_APP_NAMES[@]}"; do
                if [ "${MAS_APP_NAMES[$i]}" = "$app_name" ]; then
                    install_mas_app "${MAS_APP_IDS[$i]}" "$app_name" "$INSTALLED_APPS"
                    break
                fi
            done
        done <<< "$SELECTED_APPS"
    else
        log warn "No apps selected, skipping Mac App Store installations"
    fi
else
    log info "Installing Mac App Store applications..."
    for i in "${!MAS_APP_IDS[@]}"; do
        install_mas_app "${MAS_APP_IDS[$i]}" "${MAS_APP_NAMES[$i]}" "$INSTALLED_APPS"
    done
fi

DEFAULT_WORKSPACE="$HOME/workspace"
WORKSPACE_DIR=$(input "Workspace directory:" "$DEFAULT_WORKSPACE")

if [ ! -d "$WORKSPACE_DIR" ]; then
    mkdir -p "$WORKSPACE_DIR"
    log success "Created workspace directory: $WORKSPACE_DIR"
fi

if [ "$UPDATE_MODE" != true ]; then
    if [ -f "$HOME/.zshrc" ]; then
        BACKUP_FILE="$HOME/.zshrc.backup.$(date +%s)"
        log warn "Backing up existing .zshrc to $BACKUP_FILE"
        cp "$HOME/.zshrc" "$BACKUP_FILE"
    fi

    log info "Installing Zsh configuration..."
    cp "$SCRIPT_DIR/zshrc-template" "$HOME/.zshrc"
else
    log warn "Skipping .zshrc update (UPDATE_MODE)"
    log info "Updating Zsh partials..."
fi

mkdir -p "$HOME/.config/zsh"
if [ "$UPDATE_MODE" = true ]; then
    for zsh_file in "$SCRIPT_DIR/zsh/"*.zsh; do
        target="$HOME/.config/zsh/$(basename "$zsh_file")"
        if [ -e "$target" ]; then
            log warn "Skipping $(basename "$zsh_file") update (UPDATE_MODE)"
        else
            cp "$zsh_file" "$target"
        fi
    done

    if [ -e "$HOME/.zsh_plugins.txt" ]; then
        log warn "Skipping .zsh_plugins.txt update (UPDATE_MODE)"
    else
        cp "$SCRIPT_DIR/zsh_plugins.txt" "$HOME/.zsh_plugins.txt"
    fi
else
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

# Neovim configuration
if [ -d "$SCRIPT_DIR/nvim" ]; then
    mkdir -p "$HOME/.config/nvim"
    if [ "$UPDATE_MODE" = true ] && [ -e "$HOME/.config/nvim/init.lua" ]; then
        if [ -L "$HOME/.config/nvim/init.lua" ] && [ "$(readlink "$HOME/.config/nvim/init.lua")" = "$SCRIPT_DIR/nvim/init.lua" ]; then
            log success "nvim config already linked"
        else
            log warn "Skipping nvim init.lua update (UPDATE_MODE)"
        fi
    else
        ln -sf "$SCRIPT_DIR/nvim/init.lua" "$HOME/.config/nvim/init.lua"
        log success "Linked nvim config"
    fi
fi

# Symlink .config folders
if [ -d "$SCRIPT_DIR/.config" ]; then
    log info "Symlinking .config folders..."
    mkdir -p "$HOME/.config"
    for config_dir in "$SCRIPT_DIR/.config"/*; do
        if [ -d "$config_dir" ]; then
            dir_name=$(basename "$config_dir")
            target="$HOME/.config/$dir_name"
            if [ -L "$target" ]; then
                log success "  $dir_name already symlinked"
            elif [ -d "$target" ]; then
                log warn "  $dir_name exists (not a symlink), linking contents"
                while IFS= read -r -d '' item; do
                    rel_path="${item#"$config_dir"/}"
                    target_item="$target/$rel_path"
                    if [ -L "$target_item" ]; then
                        log success "    $rel_path already symlinked"
                    elif [ -e "$target_item" ]; then
                        log warn "    $rel_path exists (not a symlink), skipping"
                    else
                        mkdir -p "$(dirname "$target_item")"
                        ln -s "$item" "$target_item"
                        log success "    Linked $rel_path"
                    fi
                done < <(find "$config_dir" -type f -print0)
            else
                ln -s "$config_dir" "$target"
                log success "  Linked $dir_name"
            fi
        fi
    done
fi

# Symlink AI tooling directories for each provider
# Format: "target_path:source_name"
# target_path supports ~ for home directory
AI_TOOLING_MAPPINGS=(
    # OpenCode (~/.config/opencode/)
    "~/.config/opencode/agents:agents"
    "~/.config/opencode/command:commands"
    "~/.config/opencode/skill:skills"
    "~/.config/opencode/INSTRUCTIONS.md:INSTRUCTIONS.md"
    # Claude (~/.claude/)
    "~/.claude/agents:agents"
    "~/.claude/hooks:hooks"
    "~/.claude/commands:commands"
    "~/.claude/skills:skills"
    "~/.claude/CLAUDE.md:INSTRUCTIONS.md"
    "~/.claude/settings.json:claude-settings.json"
    # Codex (~/.codex/)
    "~/.codex/skills:skills"
    "~/.codex/AGENTS.md:INSTRUCTIONS.md"
    # Copilot (~/.copilot/)
    "~/.copilot/agents:agents"
    "~/.copilot/skills:skills"
    "~/.copilot/copilot-instructions.md:INSTRUCTIONS.md"
    # Gemini (~/.gemini/)
    "~/.gemini/skills:skills"
    "~/.gemini/GEMINI.md:INSTRUCTIONS.md"
)

if [ -d "$SCRIPT_DIR/ai-tooling" ]; then
    log info "Symlinking AI tooling..."
    for mapping in "${AI_TOOLING_MAPPINGS[@]}"; do
        IFS=':' read -r target_path src_name <<< "$mapping"
        src_path="$SCRIPT_DIR/ai-tooling/$src_name"
        target="${target_path/#\~/$HOME}"
        target_dir=$(dirname "$target")
        target_name=$(basename "$target")

        if [ -e "$src_path" ]; then
            mkdir -p "$target_dir"
            if [ -L "$target" ]; then
                log success "  $target_name already symlinked"
            elif [ -e "$target" ]; then
                log warn "  $target_name exists (not a symlink), skipping"
            else
                ln -s "$src_path" "$target"
                log success "  Linked $target_name -> $src_name"
            fi
        fi
    done
fi

# Tmux configuration
if [ -f "$SCRIPT_DIR/tmux.conf" ]; then
    if [ "$UPDATE_MODE" = true ] && [ -e "$HOME/.tmux.conf" ]; then
        if [ -L "$HOME/.tmux.conf" ] && [ "$(readlink "$HOME/.tmux.conf")" = "$SCRIPT_DIR/tmux.conf" ]; then
            log success "tmux.conf already linked"
        else
            log warn "Skipping tmux.conf update (UPDATE_MODE)"
        fi
    else
        ln -sf "$SCRIPT_DIR/tmux.conf" "$HOME/.tmux.conf"
        log success "Linked tmux.conf"
    fi
fi

if [ ! -d "$HOME/.cargo" ]; then
    spin "Installing Rust..." bash -c 'curl --proto "=https" --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable'
    . "$HOME/.cargo/env"
fi

if [ "$UPDATE_MODE" != true ]; then
    if confirm "Apply macOS defaults (Finder, Dock, keyboard settings)?"; then
        spin "Applying macOS defaults..." bash "$SCRIPT_DIR/macos-defaults.sh"
    fi
fi

# AI CLI Tools
AI_TOOLS=(
    "Claude Code"
    "GitHub Copilot CLI"
    "Gemini CLI"
    "OpenAI Codex"
    "OpenCode"
)

install_ai_tool() {
    local tool=$1
    case "$tool" in
        "Claude Code")
            if ! command -v claude &> /dev/null; then
                spin "Installing Claude Code..." bash -c 'curl -fsSL https://claude.ai/install.sh | bash'
            else
                log success "Claude Code already installed"
            fi
            ;;
        "GitHub Copilot CLI")
            if ! command -v copilot &> /dev/null; then
                spin "Installing GitHub Copilot CLI..." bash -c 'curl -fsSL https://gh.io/copilot-install | bash'
            else
                log success "GitHub Copilot CLI already installed"
            fi
            ;;
        "Gemini CLI")
            if ! command -v gemini &> /dev/null; then
                spin "Installing Gemini CLI..." npm install -g @google/gemini-cli
            else
                log success "Gemini CLI already installed"
            fi
            ;;
        "OpenAI Codex")
            if ! command -v codex &> /dev/null; then
                spin "Installing OpenAI Codex..." brew install --cask codex
            else
                log success "OpenAI Codex already installed"
            fi
            ;;
        "OpenCode")
            if ! command -v opencode &> /dev/null; then
                spin "Installing OpenCode..." bash -c 'curl -fsSL https://opencode.ai/install | bash'
            else
                log success "OpenCode already installed"
            fi
            ;;
    esac
}

echo ""
if $HAS_GUM; then
    log info "Select AI CLI tools to install (optional):"
    SELECTED_AI_TOOLS=$(printf '%s\n' "${AI_TOOLS[@]}" | gum choose --no-limit --header "Space to select, Enter to confirm (or just Enter to skip)")

    if [ -n "$SELECTED_AI_TOOLS" ]; then
        while IFS= read -r tool; do
            install_ai_tool "$tool"
        done <<< "$SELECTED_AI_TOOLS"
    else
        log warn "No AI tools selected, skipping"
    fi
else
    if confirm "Install AI CLI tools?"; then
        echo "Available tools:"
        for i in "${!AI_TOOLS[@]}"; do
            echo "  $((i+1)). ${AI_TOOLS[$i]}"
        done
        echo ""
        log info "Run setup again with gum installed for multi-select, or install manually"
    fi
fi

echo ""
log_banner rounded "Verifying Installation"
echo ""

VERIFICATION_DATA=()

verify_command() {
    local cmd=$1
    local name=$2
    local version=""

    if command -v "$cmd" &> /dev/null; then
        case "$cmd" in
            go)   version=$(go version 2>&1 | head -n 1) ;;
            melt) version=$(melt version 2>&1 | head -n 1 || echo "installed") ;;
            soft) version=$(soft version 2>&1 | head -n 1 || echo "installed") ;;
            *)
                version=$($cmd --version 2>&1 | head -n 1)
                if [[ $version == *"unknown"* ]] || [[ $version == *"illegal"* ]] || [[ $version == *"Error"* ]]; then
                    version=$($cmd -version 2>&1 | head -n 1 || echo "installed")
                fi
                ;;
        esac

        if [[ $version == *"Error"* ]] || [[ $version == *"unknown"* ]] || [[ $version == *"illegal"* ]]; then
            version="installed"
        fi

        if $HAS_GUM; then
            VERIFICATION_DATA+=("$name|✓|$version")
        else
            echo "✓ $name: $version"
        fi
        return 0
    else
        if $HAS_GUM; then
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
if $HAS_GUM; then
    gum format -- "# Setup Complete!" \
        "" \
        "Your machine has been successfully configured!" \
        "" \
        "## Summary" \
        "- **Mode**: $([ "$UPDATE_MODE" = true ] && echo "UPDATE" || echo "FULL SETUP")" \
        "- **Workspace**: \`$WORKSPACE_DIR\`" \
        "- **Log File**: \`$LOG_FILE\`" \
        "" \
        "## Next Steps" \
        "1. Restart your terminal or run: \`source ~/.zshrc\`" \
        "2. Verify your setup with: \`which fnm\` and other tools" \
        "3. Customize your \`.zshrc\` as needed" \
        "" \
        "## Useful Commands" \
        "- \`brew update && brew upgrade\` - Update packages" \
        "- \`gh auth login\` - Authenticate with GitHub"
else
    echo "=== Setup Complete! ==="
    echo "Mode: $([ "$UPDATE_MODE" = true ] && echo "UPDATE" || echo "FULL SETUP")"
    echo "Workspace: $WORKSPACE_DIR"
    echo "Log file: $LOG_FILE"
    echo ""
    echo "Next steps:"
    echo "  1. Restart your terminal or run: source ~/.zshrc"
    echo "  2. Verify your setup with: which fnm"
    echo "  3. Customize your .zshrc as needed"
fi
echo ""

sudo -k
