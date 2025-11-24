# Machine Setup

A simple set of scripts to install commonly used dependencies on my machines, this is particularly useful when I get a new MacBook or I reinstall Mac OS from fresh, which I do a lot.

## Quick Start

### Fresh Installation

```bash
# Clone this repository
git clone https://github.com/nicholasgriffin/machine-setup.git
cd machine-setup

# Install gum if you don't have it already
brew install gum

# Run the setup
sh ./setup.sh
```

### With Git Configuration

The setup script will prompt you to configure Git and GPG signing. If you choose yes:

**Prerequisites**: You must configure your Git identity first:

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

Then run setup:

```bash
sh ./setup.sh
```
