# Zshrc Quick Reference Card

## 🚀 Most Useful Commands

| Command            | What It Does                                       |
| ------------------ | -------------------------------------------------- |
| `proj`             | Fuzzy search and jump to any project               |
| `cd projectname`   | Smart jump to frequently used directories (zoxide) |
| `ll`               | List files with icons, git status, details         |
| `lt`               | Show directory as a tree                           |
| `rgs "text"`       | Search for text in all files                       |
| `rge "text"`       | Search for text and open file in editor            |
| `up 3`             | Go up 3 directories                                |
| `..` / `...`       | Go up 1/2 directories                              |
| `gwt`              | List git worktrees                                 |
| `gwtcd`            | Fuzzy search and jump to a worktree                |
| `killport 3000`    | Kill process on port 3000                          |
| `mkcd dirname`     | Make directory and cd into it                      |
| `extract file.zip` | Extract any archive type                           |
| `cpath`            | Copy current path to clipboard                     |
| `cfile file.txt`   | Copy file content to clipboard                     |
| `brewdump`         | Save current Homebrew packages to Brewfile         |

## 🎨 Charm CLI Tools

### Soft Serve (Git Server)

| Command        | What It Does                                            |
| -------------- | ------------------------------------------------------- |
| `serve`        | Smart serve: git server in repos, HTTP server elsewhere |
| `serve-start`  | Start Soft Serve git server in background               |
| `serve-stop`   | Stop Soft Serve server                                  |
| `serve-browse` | Browse repos via SSH TUI                                |

### Skate (Key-Value Store)

| Command                             | What It Does           |
| ----------------------------------- | ---------------------- |
| `note mykey "value"`                | Save a note            |
| `note mykey`                        | Get a note             |
| `note list`                         | List all notes         |
| `note delete mykey`                 | Delete a note          |
| `snippet deploy "kubectl apply -f"` | Save a command snippet |
| `snippet deploy`                    | Get a snippet          |
| `snippet list`                      | List all snippets      |
| `config api_key "xxx"`              | Save a config value    |
| `config api_key`                    | Get a config value     |
| `config list`                       | List all configs       |

### Melt (SSH Key Backup)

| Command                        | What It Does                          |
| ------------------------------ | ------------------------------------- |
| `ssh-backup`                   | Backup default SSH key to seed phrase |
| `ssh-backup ~/.ssh/custom_key` | Backup specific key                   |
| `ssh-restore`                  | Restore key from seed phrase          |
| `ssh-restore ~/.ssh/new_key`   | Restore to specific location          |

## 📁 Quick Paths

| Shortcut     | Goes To                          |
| ------------ | -------------------------------- |
| `~workspace` | ~/workspace                      |
| `~github`    | ~/Documents/GitHub               |
| `~setup`     | ~/Documents/GitHub/machine-setup |

**Usage:** `cd ~workspace` or `cd ~github/myproject`

## 🔧 Git Shortcuts

| Shortcut      | Full Command                         |
| ------------- | ------------------------------------ |
| `lg`          | lazygit (full TUI)                   |
| `gs`          | git status                           |
| `ga .`        | git add .                            |
| `gc -m "msg"` | git commit -m "msg"                  |
| `gp`          | git pull                             |
| `gph`         | git push                             |
| `gco branch`  | git checkout branch                  |
| `gd`          | git diff                             |
| `gl`          | git log --oneline --graph --decorate |
| `gla`         | git log (beautiful with colors)      |
| `gb`          | git branch                           |
| `ghstats`     | Show GitHub repo stats               |

## 🐳 Docker Shortcuts

| Shortcut | What It Does                                   |
| -------- | ---------------------------------------------- |
| `dps`    | Show running containers                        |
| `dimg`   | Show images                                    |
| `dlogs`  | Follow container logs                          |
| `dexec`  | Execute command in container                   |
| `dclean` | ⚠️ Remove ALL unused containers/images/volumes |
| `dstop`  | Stop all running containers                    |
| `drm`    | Remove all containers                          |

## 📦 NPM/PNPM Shortcuts

| NPM   | PNPM  | What It Does       |
| ----- | ----- | ------------------ |
| `ni`  | `pi`  | install            |
| `nid` | `pid` | install --save-dev |
| `nrd` | `prd` | run dev            |
| `nrb` | `prb` | run build          |
| `nrt` | `prt` | run test           |

## 🚀 Productivity Boosters

| Feature            | How to use                                                                      |
| ------------------ | ------------------------------------------------------------------------------- |
| **Magic Enter**    | Press `Enter` on empty line to run `ls` (or `git status` in repos)              |
| **Global Aliases** | Pipe easily: `history G docker` (grep), `cat file L` (less), `echo hi C` (copy) |
| **Suffix Aliases** | Open files directly: type `README.md` → opens in vim                            |
| **Safety**         | `rm`, `cp`, `mv` now ask for confirmation before overwriting                    |

## ⌨️ Keyboard Shortcuts

| Keys              | What It Does                                   |
| ----------------- | ---------------------------------------------- |
| `jk`              | Exit insert mode (instead of ESC)              |
| `Ctrl+R`          | Search command history (Atuin - synced fuzzy!) |
| `Ctrl+T`          | Search files (fuzzy)                           |
| `↑` / `↓`         | Browse history matching what you typed         |
| `→`               | Accept auto-suggestion                         |
| `v` (normal mode) | Edit command in vim                            |

## 🎯 Tips

1. **Type part of a command, then ↑** - Only shows matching history (or use Ctrl+R with Atuin!)
2. **Just type `cd name`** - It learns your most-used directories (zoxide)
3. **Type `ll` in git repos** - See git status alongside files
4. **Use `proj`** - When you forget where a project is
5. **Use `..` shortcuts** - Faster than typing `cd ../..`
6. **Use `cat` on code files** - Now has syntax highlighting (bat)
7. **Use `gwt` for multi-branch work** - No more stashing
8. **Try `lg` instead of git commands** - LazyGit
9. **Use `man <cmd>` for a better `man`** - Get simple examples first
10. **Share files with `transfer`** - Quick shares

## 🔍 Search

```bash
# Search for text in files
rgs "TODO"

# Search and open in editor
rge "function handleSubmit"

# Search command history
Ctrl+R, then type what you remember

# Search files
Ctrl+T, then type filename
```

## 🛠️ Maintenance

```bash
reload          # Reload .zshrc after changes
zshrc           # Edit .zshrc
brewdump        # Update Brewfile with current packages
```

## 🖥️ Tmux

**Shell aliases:**

| Command        | What It Does                              |
| -------------- | ----------------------------------------- |
| `tn mysession` | Create new tmux session named "mysession" |
| `ta mysession` | Attach to existing session                |
| `tl`           | List all tmux sessions                    |
| `tk mysession` | Kill a tmux session                       |

**Inside tmux (prefix is `Ctrl+a`):**

| Keys          | What It Does               |
| ------------- | -------------------------- |
| `C-a c`       | New window                 |
| `C-a "`       | Split horizontal           |
| `C-a %`       | Split vertical             |
| `C-a h/j/k/l` | Navigate panes (vim-style) |
| `C-a H/J/K/L` | Resize panes               |
| `C-a Tab`     | Last window                |
| `C-a Escape`  | Enter copy mode            |
| `C-a r`       | Reload config              |

Config auto-installed to `~/.tmux.conf` by setup script.

## 💎 Ruby (rbenv)

| Command               | What It Does                           |
| --------------------- | -------------------------------------- |
| `rbenv versions`      | List installed Ruby versions           |
| `rbenv install 3.2.0` | Install a Ruby version                 |
| `rbenv global 3.2.0`  | Set global Ruby version                |
| `rbenv local 3.2.0`   | Set Ruby version for current directory |

## 📦 Node.js (fnm)

| Command          | What It Does                 |
| ---------------- | ---------------------------- |
| `fnm list`       | List installed Node versions |
| `fnm install 20` | Install Node v20             |
| `fnm use 20`     | Switch to Node v20           |
| `fnm default 20` | Set default Node version     |

Note: fnm auto-switches Node version when entering a directory with `.node-version` or `.nvmrc`

## 🕐 Timestamp Utilities

| Command              | What It Does                       |
| -------------------- | ---------------------------------- |
| `unixts`             | Get current Unix timestamp         |
| `iso8601`            | Get current ISO 8601 timestamp     |
| `mins-ago 30`        | Unix timestamp from 30 minutes ago |
| `hours-ago 2`        | Unix timestamp from 2 hours ago    |
| `yesterday`          | Unix timestamp for yesterday       |
| `time-at 1704067200` | Convert Unix timestamp to readable |

## 🍎 macOS Utilities

| Command       | What It Does                        |
| ------------- | ----------------------------------- |
| `flush-dns`   | Flush DNS cache (requires sudo)     |
| `get-new-mac` | Generate random MAC address for en0 |
| `airport`     | Access macOS airport utility        |
| `trim_path`   | Remove duplicate entries from PATH  |

Note: SSH key is auto-added to macOS keychain on shell start

## 📝 Neovim

**Leader key is `Space`**

| Keys          | What It Does                |
| ------------- | --------------------------- |
| `<leader>f`   | Find files (telescope)      |
| `<leader>g`   | Live grep (search in files) |
| `<leader>b`   | Switch buffers              |
| `<leader>e`   | File explorer               |
| `<leader>w`   | Save file                   |
| `<leader>h`   | Clear search highlight      |
| `<leader>n/p` | Next/previous buffer        |
| `<leader>q`   | Close buffer                |
| `C-h/j/k/l`   | Navigate splits             |
| `gcc`         | Comment line                |
| `gc`          | Comment selection (visual)  |

Plugins auto-install on first launch via lazy.nvim.

## ⚡ Other Stuff

| Command                          | What It Does                                |
| -------------------------------- | ------------------------------------------- |
| `lg`                             | Launch LazyGit - git TUI                    |
| `vim` / `vi`                     | Launch Neovim (aliased from vim/vi)         |
| `help <cmd>`                     | Show simple examples for any command (tldr) |
| `top`                            | Launch btop/htop - system monitor           |
| `cheat tar`                      | Get cheatsheet for any command              |
| `qr "text"`                      | Generate QR code in terminal                |
| `transfer file.zip`              | Upload file, get shareable link (24hrs)     |
| `ghstats`                        | Show current repo GitHub stats              |
| `gla`                            | Beautiful git log with graph                |
| `myip`                           | Show your public IP with location           |
| `pingweb url`                    | Test website response time                  |
| `biggies`                        | Find 10 largest files/folders here          |
| `whois-port 3000`                | See what's running on a port                |
| `dclean-safe`                    | Safe Docker cleanup with preview            |
| `get api.example.com`            | Quick HTTP GET request                      |
| `post api.example.com key=value` | Quick HTTP POST                             |
| `wrk -t2 -c10 -d5s url`          | HTTP benchmarking                           |
| `websocat ws://url`              | WebSocket client                            |
