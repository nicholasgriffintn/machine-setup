# Zshrc Quick Reference Card

## 🚀 Most Useful Commands

| Command | What It Does |
|---------|-------------|
| `proj` | Fuzzy search and jump to any project |
| `cd projectname` | Smart jump to frequently used directories (zoxide) |
| `ll` | List files with icons, git status, details |
| `lt` | Show directory as a tree |
| `rgs "text"` | Search for text in all files |
| `rge "text"` | Search for text and open file in editor |
| `up 3` | Go up 3 directories |
| `..` / `...` | Go up 1/2 directories |
| `gwt` | List git worktrees |
| `gwtcd` | Fuzzy search and jump to a worktree |
| `killport 3000` | Kill process on port 3000 |
| `mkcd dirname` | Make directory and cd into it |
| `extract file.zip` | Extract any archive type |
| `cpath` | Copy current path to clipboard |
| `cfile file.txt` | Copy file content to clipboard |
| `brewdump` | Save current Homebrew packages to Brewfile |

## 📁 Quick Paths

| Shortcut | Goes To |
|----------|---------|
| `~workspace` | ~/workspace |
| `~github` | ~/Documents/GitHub |
| `~setup` | ~/Documents/GitHub/machine-setup |

**Usage:** `cd ~workspace` or `cd ~github/myproject`

## 🔧 Git Shortcuts

| Shortcut | Full Command |
|----------|--------------|
| `gs` | git status |
| `ga .` | git add . |
| `gc -m "msg"` | git commit -m "msg" |
| `gp` | git pull |
| `gph` | git push |
| `gco branch` | git checkout branch |
| `gd` | git diff |
| `gl` | git log --oneline --graph --decorate |
| `gb` | git branch |

## 🐳 Docker Shortcuts

| Shortcut | What It Does |
|----------|-------------|
| `dps` | Show running containers |
| `dimg` | Show images |
| `dlogs` | Follow container logs |
| `dexec` | Execute command in container |
| `dclean` | ⚠️ Remove ALL unused containers/images/volumes |
| `dstop` | Stop all running containers |
| `drm` | Remove all containers |

## 📦 NPM/PNPM Shortcuts

| NPM | PNPM | What It Does |
|-----|------|-------------|
| `ni` | `pi` | install |
| `nid` | `pid` | install --save-dev |
| `nrd` | `prd` | run dev |
| `nrb` | `prb` | run build |
| `nrt` | `prt` | run test |

## 🚀 Productivity Boosters

| Feature | How to use |
|---------|------------|
| **Magic Enter** | Press `Enter` on empty line to run `ls` (or `git status` in repos) |
| **Global Aliases** | Pipe easily: `history G docker` (grep), `cat file L` (less), `echo hi C` (copy) |
| **Suffix Aliases** | Open files directly: type `README.md` → opens in vim |
| **Safety** | `rm`, `cp`, `mv` now ask for confirmation before overwriting |

## ⌨️ Keyboard Shortcuts

| Keys | What It Does |
|------|-------------|
| `jk` | Exit insert mode (instead of ESC) |
| `Ctrl+R` | Search command history (fuzzy) |
| `Ctrl+T` | Search files (fuzzy) |
| `↑` / `↓` | Browse history matching what you typed |
| `→` | Accept auto-suggestion |
| `v` (normal mode) | Edit command in vim |

## 🎯 Tips

1. **Type part of a command, then ↑** - Only shows matching history
2. **Just type `cd name`** - It learns your most-used directories (zoxide)
3. **Type `ll` in git repos** - See git status alongside files
4. **Use `proj`** - When you forget where a project is
5. **Use `..` shortcuts** - Faster than typing `cd ../..`
6. **Use `cat` on code files** - Now has syntax highlighting
7. **Use `gwt` for multi-branch work** - No more stashing

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

---
