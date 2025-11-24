# Machine Setup

A simple set of scripts to install commonly used dependencies on my machines, this is particularly useful when I get a new MacBook or I reinstall Mac OS from fresh, which I do a lot.

## Quick Start

### Fresh Installation

```bash
# Clone this repository
git clone <your-repo-url>
cd machine-setup

# Run the setup
sh ./setup.sh
```

### With Git Configuration

```bash
# First, configure your Git identity
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Then run setup with Git configuration enabled
CONFIGURE_GIT=true sh ./setup.sh
```

### Update Existing Setup

If you've already run the setup and want to update packages:

```bash
sh ./setup.sh
# When prompted, choose 'Y' for UPDATE mode
```

## Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CONFIGURE_GIT` | `false` | Enable Git and GPG setup |
| `SKIP_MAC_INSTALLS` | `false` | Skip Mac App Store installations |
| `SKIP_BACKUP` | `false` | Skip backing up existing configs |
| `UPDATE_MODE` | `false` | Run in update mode (auto-detected) |

### Examples

```bash
# Skip Mac App Store apps
SKIP_MAC_INSTALLS=true sh ./setup.sh

# Full setup with Git configuration
CONFIGURE_GIT=true sh ./setup.sh

# Force update mode
UPDATE_MODE=true sh ./setup.sh
```

## What Gets Installed

### Command-Line Tools (via Homebrew)

- **Languages**: Python, Go, Node.js (NVM), Rust
- **Package Managers**: poetry, pnpm, yarn, nvm
- **Version Control**: git, git-secrets, gh (GitHub CLI)
- **Cloud/DevOps**: awscli, podman, podman-compose, docker
- **Security**: mkcert, certbot, gpg-suite
- **Utilities**: jq, coreutils, mas, sqlite, neofetch, oh-my-posh

### GUI Applications (via Homebrew Casks)

- **Development**: Visual Studio Code, Docker Desktop
- **Browsers**: Google Chrome, Firefox
- **Productivity**: Obsidian, Raycast, Slack
- **Fonts**: FiraCode, Meslo Nerd Font, Fantasque Sans Mono Nerd Font
- **File Management**: Dropbox, Dropbox Capture
- **Media**: VLC
- **Hardware**: Logi Options+

### Mac App Store Apps

- Magnet (window manager)
- Forklift (file manager)
- Microsoft Office (Word, Excel, PowerPoint)
- YubiKey Personalization Tool
- Unsplash Wallpapers
- Home Assistant
- Runcat (system monitor)
- Pandan (time awareness)

## Directory Structure

```
machine-setup/
├── setup.sh                    # Main entry point
├── machine-setup.sh           # Core installation script
├── git-setup.sh               # Git and GPG configuration
├── Brewfile                   # Homebrew package definitions
├── Brewfile.lock.json         # Locked package versions
├── zshrc-template             # Zsh configuration template
├── catppuccin_mocha-zsh-syntax-highlighting.zsh  # Theme
└── README.md                  # This file
```

## Post-Installation

After setup completes:

1. **Restart your terminal** or run: `source ~/.zshrc`
2. Review the log file: `cat ~/machine-setup.log`
3. Verify installations with the output summary

### Created Files & Directories

- `~/.zshrc` - Zsh configuration (backed up if exists)
- `~/.zprofile` - Homebrew environment
- `~/.bin/antigen/` - Antigen plugin manager
- `~/.nvm/` - Node Version Manager
- `~/.cargo/` - Rust toolchain
- `~/workspace/` - Development workspace
- `~/machine-setup.log` - Setup log file

## Shell Features

The configured Zsh environment includes:

- **Vi Mode**: Vim keybindings in the shell
- **Oh-My-Posh**: Beautiful prompt with Catppuccin theme
- **Syntax Highlighting**: Catppuccin Mocha color scheme
- **Auto-suggestions**: Command suggestions as you type
- **Auto-completions**: Tab completion for git, docker, aws, gh, and more
- **NVM Integration**: Automatic Node version switching with `.nvmrc` files
- **Smart PATH Management**: No duplicate entries

## Git Configuration (Optional)

When `CONFIGURE_GIT=true`:

1. Sets global Git configs (push.default, fetch.prune, pull.rebase, diff.colorMoved)
2. Generates 4096-bit RSA GPG key
3. Configures Git to sign commits automatically
4. Exports public key to clipboard
5. Opens GitHub GPG settings for you to add the key

**Prerequisites**: Must have `user.name` and `user.email` configured first.

## Update Mode

When running on an already-configured machine:

- **Auto-detected**: Checks for existing Oh-My-Posh setup
- **Safe**: Won't overwrite `~/.zshrc` or other configs
- **Updates**: Refreshes Homebrew packages, Antigen, and other tools
- **Idempotent**: Can run multiple times safely

## Troubleshooting

### Common Issues

**"Homebrew not found"**:
Restart terminal or run: `eval "$(/opt/homebrew/bin/brew shellenv)"`

**"Command not found" after install**:
Restart terminal or run: `source ~/.zshrc`

**Mac App Store login required**:
Sign in to the App Store before running with Mac App installs enabled

**GPG key generation fails**:
Ensure git `user.name` and `user.email` are configured first

### Log Files

All output is logged to `~/machine-setup.log`. Check this file if something fails:

```bash
cat ~/machine-setup.log
# or
tail -f ~/machine-setup.log  # Follow during installation
```

## Customization

### Adding Packages

Edit [Brewfile](Brewfile) to add or remove packages:

```ruby
# Add a formula (command-line tool)
brew "package-name"

# Add a cask (GUI application)
cask "app-name"
```

### Modifying Shell Config

Edit [zshrc-template](zshrc-template) to customize your shell environment. Changes will be applied on next run (full setup mode).

### Changing Mac App Store Apps

Edit [machine-setup.sh](machine-setup.sh) lines 50-61 to modify the `MAS_APPS` array.

## Maintenance

### Updating Packages

```bash
# Update Homebrew packages
brew update && brew upgrade

# Update Node.js LTS
nvm install --lts
nvm alias default lts/*

# Update Rust
rustup update

# Update Antigen plugins
antigen update
```

### Cleaning Up

```bash
# Clean Homebrew cache
brew cleanup

# Remove old backups
rm ~/.zshrc.backup.*
```
