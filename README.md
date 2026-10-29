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

### Editor and Terminal

VS Code used to drift -- the theme and fonts would reset every few days. Three things caused it, and `vscode/settings.json` plus `scripts/sync-vscode.py` fix all three:

- Nothing pinned `workbench.colorTheme` or any font family, so VS Code quietly fell back to Dark+ and the default fonts whenever a theme extension updated.
- `window.autoDetectColorScheme` follows the macOS appearance, which is a second, invisible owner of the theme. It's now explicitly off.
- Settings Sync merges stable and Insiders into one bucket, so the last window you closed won. The repo is now the tiebreaker.

`machine-setup.sh` applies this on every run. To re-apply without a full setup:

```bash
# Apply the baseline to stable, Insiders, and every profile under each
python3 scripts/sync-vscode.py

# See what would change first
python3 scripts/sync-vscode.py --dry-run
```

It merges rather than overwrites: only the keys the repo defines are touched, so machine-local values (agent sandbox paths, per-machine `typescript.tsdk`) survive. The previous file is kept as `settings.json.bak`. `vscode/extensions.txt` lists the extensions it installs, including the Catppuccin theme the settings depend on -- a theme ID pointing at an uninstalled extension is itself a silent reset. It calls the launcher inside each app bundle, so it works on a fresh machine without first running **Install 'code' command in PATH**.

If Settings Sync keeps pulling older values back from another machine, turn `Settings` off in **Settings Sync: Configure** and let this repo own them.

Ghostty's config lives at `.config/ghostty/config`, which `~/.config/ghostty` symlinks to, so a change here lands on the next launch. Ghostty drops values it can't parse without erroring -- `window-show-tab-bar = "always"`, `shell-integration-features = true` and `scrollback-limit = 50000` (that option is in bytes) all sat unapplied for months -- so check your work:

```bash
ghostty +validate-config   # syntax
ghostty +show-config       # what it actually ended up with
```

The update channel is pinned to `stable`. If Ghostty is currently on a `tip` build (check `ghostty +version`), the config won't downgrade it -- reinstall with `brew reinstall --cask ghostty`.
