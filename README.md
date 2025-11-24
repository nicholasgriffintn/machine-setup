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

## What Gets Installed

- Development tools like Python, Go, Node and Rust
- Package managers
- Version control packages
- Security services
- Various GUI applications that I use from Homebrew Casks and the Mac App Store

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
