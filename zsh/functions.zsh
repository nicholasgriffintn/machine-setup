#
# Functions
#

# Create directory and cd into it
mkcd() {
  mkdir -p "$1" && cd "$1"
}

# Extract any archive
extract() {
  if [ -f "$1" ]; then
    case "$1" in
      *.tar.bz2)   tar xjf "$1"    ;;
      *.tar.gz)    tar xzf "$1"    ;;
      *.bz2)       bunzip2 "$1"    ;;
      *.rar)       unrar x "$1"    ;;
      *.gz)        gunzip "$1"     ;;
      *.tar)       tar xf "$1"     ;;
      *.tbz2)      tar xjf "$1"    ;;
      *.tgz)       tar xzf "$1"    ;;
      *.zip)       unzip "$1"      ;;
      *.Z)         uncompress "$1" ;;
      *.7z)        7z x "$1"       ;;
      *)           echo "'$1' cannot be extracted" ;;
    esac
  else
    echo "'$1' is not a valid file"
  fi
}

# Show listening ports
ports() {
  lsof -iTCP -sTCP:LISTEN -n -P
}

# Kill process on specific port
killport() {
  if [ -z "$1" ]; then
    echo "Usage: killport <port_number>"
    return 1
  fi
  kill -9 $(lsof -ti:$1)
}

# Show external IP
myip() {
  curl -s https://api.ipify.org
  echo
}

# Git worktree helpers
unalias gwt 2>/dev/null
gwt() {
  if [ -z "$1" ]; then
    git worktree list
  else
    git worktree add "$@"
  fi
}

gwtr() {
  git worktree remove "$1"
}

gwtcd() {
  local worktree=$(git worktree list | fzf | awk '{print $1}')
  [ -n "$worktree" ] && cd "$worktree"
}

# Smart search with ripgrep
rgs() {
  if command -v rg &>/dev/null; then
    command rg --smart-case --hidden --glob '!.git' "$@"
  else
    echo "ripgrep not installed"
  fi
}

# Search and edit with fzf
rge() {
  if ! command -v rg &>/dev/null || ! command -v fzf &>/dev/null; then
    echo "Requires ripgrep and fzf"
    return 1
  fi
  local file=$(rg --files-with-matches --no-messages "$1" | fzf --preview "rg --color=always --context=3 '$1' {}")
  [ -n "$file" ] && $EDITOR "$file"
}

# Quick project switcher
proj() {
  if ! command -v fd &>/dev/null || ! command -v fzf &>/dev/null; then
    echo "Requires fd and fzf"
    return 1
  fi
  local project=$(fd --type d --max-depth 3 --hidden --exclude .git . ~/workspace ~/Documents/GitHub | fzf --preview 'eza --tree --level=1 --icons {} 2>/dev/null || ls -la {}')
  [ -n "$project" ] && cd "$project"
}

# Homebrew bundle dump automation
brewdump() {
  brew bundle dump --file=~/Documents/GitHub/machine-setup/Brewfile --force
  echo "✅ Brewfile updated"
}

# Smart up function
up() {
  local d=""
  local limit=${1:-1} # Default to 1 level
  for ((i=1 ; i <= limit ; i++)); do
    d=$d/..
  done
  d=$(echo $d | sed 's/^\///')
  if [ -z "$d" ]; then
    d=..
  fi
  cd $d
}

# Magic Enter
function magic-enter {
  if [[ -z $BUFFER ]]; then
    echo ""
    if (( $+commands[git] )) && git rev-parse --is-inside-work-tree &>/dev/null; then
      git status
    elif command -v eza &>/dev/null; then
      eza --icons --group-directories-first
    else
      ls
    fi
    zle redisplay
  else
    zle accept-line
  fi
}

