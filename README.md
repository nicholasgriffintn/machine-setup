# Machine Setup

A simple set of scripts to install commonly used dependencies on my machines, this is particularly useful when I get a new MacBook or I reinstall Mac OS from fresh, which I do a lot.

## Quick Start

### Fresh Installation

```bash
# Clone this repository
git clone https://github.com/nicholasgriffintn/machine-setup.git
cd machine-setup

# Install gum if you don't have it already (optional -- setup falls back
# to plain prompts without it, gum just makes them nicer)
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

### AI Coding Agent Bot Identity

By default, an AI coding agent working in a repo commits and pushes as you. That's fine until it does something you didn't review closely enough -- there's no separation between "you approved this" and "the agent decided this on its own." This setup can instead give AI harnesses (Claude Code, Codex) their own GitHub identity, nicknamed "Nicholas' Clanker", so their commits, pushes, and PRs are clearly attributed to the bot rather than to you, and are scoped to a single allowed GitHub owner (`AI_GIT_ALLOWED_OWNERS` in `ai-tooling/claude-settings.json`) so the agent can't push anywhere else.

**Prerequisites**: a [GitHub App](https://github.com/settings/apps) already created, installed on the repos you want it to touch, with a private key generated and downloaded from its General settings page.

`machine-setup.sh` prompts for the App ID and the path to the downloaded `.pem` on a fresh run (skipped automatically once already configured). To set it up later, or reconfigure it, replace the App ID and key path below with your own values and run:

```bash
python3 ai-tooling/scripts/set-ai-env.py \
    GITHUB_APP_ID=123456 \
    GITHUB_APP_PRIVATE_KEY_PATH=~/.config/machine-setup/nicholas-clanker.pem

# Only needed if you also use Codex:
python3 ai-tooling/scripts/sync-codex-env.py

# Starts the 30-minute token refresh described below:
bash ai-tooling/scripts/install-gh-token-refresher.sh
```

(This is the same sequence `machine-setup.sh` runs after the prompt -- `set-ai-env.py` alone only updates the config, it doesn't sync Codex or install the refresher.)

A few things worth knowing if you're touching this system:

- **`ai-tooling/claude-settings.json`** (git-tracked) holds the App ID and the private key's _path_ -- never the key itself. **`ai-tooling/claude-settings.local.json`** (gitignored) holds anything that's a live credential, e.g. a refreshed `GH_TOKEN`. Both get merged into `~/.claude/settings.json` by `ai-tooling/scripts/render-claude-settings.py`, and mirrored into `~/.codex/config.toml` by `ai-tooling/scripts/sync-codex-env.py` -- those rendered files, not the repo, are what Claude Code and Codex actually read.
- A `launchd` agent (`com.nicholasgriffin.machine-setup.refresh-gh-token`) mints a fresh installation token every 30 minutes, since GitHub App tokens expire in about an hour. Its logs are at `~/Library/Logs/machine-setup/refresh-gh-token.log`.
- To stop it: `launchctl unload ~/Library/LaunchAgents/com.nicholasgriffin.machine-setup.refresh-gh-token.plist`.
