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
    if (( $+commands[git] )) && git rev-parse --is-inside-work-tree &> /dev/null; then
      git status
    elif command -v eza &> /dev/null; then
      eza --icons --group-directories-first
    else
      ls
    fi
    zle redisplay
  else
    zle accept-line
  fi
}

#
# Charm CLI Tools Functions
#

# Soft Serve - Git Server
# Smart serve function - detects git repos and uses soft-serve, otherwise python server
smart-serve() {
  if git rev-parse --is-inside-work-tree &> /dev/null; then
    echo "🍦 Starting Soft Serve git server..."
    soft serve .
  else
    echo "🌐 Starting Python HTTP server on port ${1:-8000}..."
    python3 -m http.server "${1:-8000}"
  fi
}

# Start soft serve as a background service
serve-start() {
  if command -v soft &> /dev/null; then
    echo "🍦 Starting Soft Serve server..."
    soft serve &
    echo "Git server running! Access via: ssh localhost -p 23231"
  else
    echo "soft-serve not installed. Run: brew install soft-serve"
  fi
}

# Stop soft serve
serve-stop() {
  pkill -f "soft serve" && echo "✓ Soft Serve stopped" || echo "No Soft Serve process found"
}

# Browse repos with soft serve
serve-browse() {
  if command -v soft &> /dev/null; then
    ssh localhost -p 23231
  else
    echo "soft-serve not installed. Run: brew install soft-serve"
  fi
}

# Skate - Key-Value Store
# Quick note taking
note() {
  if ! command -v skate &> /dev/null; then
    echo "skate not installed. Run: brew install skate"
    return 1
  fi
  
  if [ -z "$1" ]; then
    echo "Usage: note <key> [value]"
    echo "       note <key>        - Get note"
    echo "       note list         - List all notes"
    echo "       note delete <key> - Delete note"
    return 1
  fi
  
  case "$1" in
    list)
      skate list
      ;;
    delete)
      skate delete "$2"
      ;;
    *)
      if [ -z "$2" ]; then
        skate get "$1"
      else
        shift
        skate set "$1" "$*"
      fi
      ;;
  esac
}

# Save a snippet
snippet() {
  if ! command -v skate &> /dev/null; then
    echo "skate not installed. Run: brew install skate"
    return 1
  fi
  
  if [ -z "$1" ]; then
    echo "Usage: snippet <name> <command>"
    echo "       snippet <name>  - Get snippet"
    echo "       snippet list    - List all snippets"
    return 1
  fi
  
  if [ "$1" = "list" ]; then
    skate list | grep "^snippet:"
  elif [ -z "$2" ]; then
    skate get "snippet:$1"
  else
    shift
    skate set "snippet:$1" "$*"
    echo "✓ Snippet saved: $1"
  fi
}

# Quick config storage
config() {
  if ! command -v skate &> /dev/null; then
    echo "skate not installed. Run: brew install skate"
    return 1
  fi
  
  if [ -z "$1" ]; then
    echo "Usage: config <key> [value]"
    echo "       config list - List all configs"
    return 1
  fi
  
  if [ "$1" = "list" ]; then
    skate list | grep "^config:"
  elif [ -z "$2" ]; then
    skate get "config:$1"
  else
    shift
    skate set "config:$1" "$*"
    echo "✓ Config saved: $1"
  fi
}

# Melt - SSH Key Backup
# Backup SSH key to seed phrase
ssh-backup() {
  if ! command -v melt &> /dev/null; then
    echo "melt not installed. Run: brew install melt"
    return 1
  fi
  
  local key_file="${1:-$HOME/.ssh/id_ed25519}"
  
  if [ ! -f "$key_file" ]; then
    echo "Error: Key file not found: $key_file"
    echo "Usage: ssh-backup [path-to-private-key]"
    return 1
  fi
  
  echo "🔑 Backing up SSH key: $key_file"
  echo "⚠️  IMPORTANT: Store these words in a safe place!"
  echo ""
  melt "$key_file"
}

# Restore SSH key from seed phrase
ssh-restore() {
  if ! command -v melt &> /dev/null; then
    echo "melt not installed. Run: brew install melt"
    return 1
  fi
  
  local output_file="${1:-$HOME/.ssh/id_ed25519_restored}"
  
  echo "🔑 Restoring SSH key from seed phrase"
  echo "Enter your seed phrase when prompted..."
  echo ""
  melt -o "$output_file"
  
  if [ -f "$output_file" ]; then
    chmod 600 "$output_file"
    echo ""
    echo "✓ Key restored to: $output_file"
    echo "  Don't forget to set proper permissions and add to ssh-agent!"
  fi
}

#
# Cool Terminal Utilities
#

# Cheatsheet for any command
cheat() {
  if [ -z "$1" ]; then
    echo "Usage: cheat <command>"
    echo "Examples: cheat tar, cheat git, cheat curl"
    return 1
  fi
  curl "cheat.sh/$1"
}

# Create a QR code from text
qr() {
  if [ -z "$1" ]; then
    echo "Usage: qr <text or URL>"
    return 1
  fi
  echo "$@" | curl -F-=\<- qrenco.de
}

# Upload and share files temporarily (24hrs)
transfer() {
  if [ -z "$1" ]; then
    echo "Usage: transfer <file>"
    echo "File will be available for 24 hours"
    return 1
  fi

  if [ ! -f "$1" ]; then
    echo "Error: File not found: $1"
    return 1
  fi

  echo "📤 Uploading $(basename "$1")..."
  url=$(curl --upload-file "$1" "https://transfer.sh/$(basename "$1")")
  echo ""
  echo "✓ File uploaded!"
  echo "🔗 $url"
  echo "$url" | pbcopy
  echo "📋 URL copied to clipboard"
}

# GitHub repo stats (requires gh cli)
ghstats() {
  if ! command -v gh &>/dev/null; then
    echo "GitHub CLI not installed. Run: brew install gh"
    return 1
  fi
  gh repo view --json stargazerCount,forkCount,watchers,issues,description \
    --jq '"⭐ Stars: \(.stargazerCount)\n🔱 Forks: \(.forkCount)\n👀 Watchers: \(.watchers.totalCount)\n📋 Issues: \(.issues.totalCount)\n📝 \(.description)"'
}

# Beautiful git log
gla() {
  git log --graph --all --format=format:'%C(bold blue)%h%C(reset) - %C(bold green)(%ar)%C(reset) %C(white)%s%C(reset) %C(dim white)- %an%C(reset)%C(auto)%d%C(reset)' --abbrev-commit --date=relative
}

# Find largest files/directories
biggies() {
  du -sh * .* 2>/dev/null | sort -hr | head -${1:-10}
}

# Port check with process details
whois-port() {
  if [ -z "$1" ]; then
    echo "Usage: whois-port <port_number>"
    return 1
  fi
  echo "Checking port $1..."
  lsof -i ":$1" | awk 'NR==1 || NR==2 {print}'
}

# Docker cleanup with safety check
dclean-safe() {
  echo "📊 Current Docker usage:"
  docker system df
  echo ""
  echo "⚠️  This will remove:"
  echo "  - All stopped containers"
  echo "  - All unused networks"
  echo "  - All dangling images"
  echo "  - All build cache"
  echo "  - All unused volumes"
  echo ""

  if command -v gum &>/dev/null; then
    if gum confirm "Continue with cleanup?"; then
      docker system prune -af --volumes
      echo ""
      echo "✓ Docker cleanup complete!"
    else
      echo "Cleanup cancelled"
    fi
  else
    read -q "REPLY?Continue? (y/n) "
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
      docker system prune -af --volumes
      echo ""
      echo "✓ Docker cleanup complete!"
    else
      echo "Cleanup cancelled"
    fi
  fi
}

# Quick HTTP server with specific port
serve-http() {
  local port="${1:-8000}"
  echo "🌐 Starting HTTP server on http://localhost:$port"
  python3 -m http.server "$port"
}

# Get public IP with details
myip() {
  echo "🌍 Public IP Information:"
  curl -s https://ipinfo.io | jq -r '"IP: \(.ip)\nCity: \(.city)\nRegion: \(.region)\nCountry: \(.country)\nOrg: \(.org)"'
}

# Test website response time
pingweb() {
  if [ -z "$1" ]; then
    echo "Usage: pingweb <url>"
    return 1
  fi
  curl -o /dev/null -s -w "Response time: %{time_total}s\nHTTP code: %{http_code}\n" "$1"
}

# Get current Unix timestamp
unixts() {
  date +%s
}

# Get current ISO 8601 timestamp
iso8601() {
  date -u +'%Y-%m-%dT%H:%M:%SZ'
}

# Get Unix timestamp from N minutes ago
mins-ago() {
  if [ -z "$1" ]; then
    echo "Usage: mins-ago <minutes>"
    return 1
  fi
  echo $(($(date +%s) - 60 * $1))
}

# Get Unix timestamp from N hours ago
hours-ago() {
  if [ -z "$1" ]; then
    echo "Usage: hours-ago <hours>"
    return 1
  fi
  echo $(($(date +%s) - 3600 * $1))
}

# Get Unix timestamp for yesterday
yesterday() {
  echo $(($(date +%s) - 86400))
}

# Convert Unix timestamp to human readable
time-at() {
  if [ -z "$1" ]; then
    echo "Usage: time-at <unix_timestamp>"
    return 1
  fi
  date -r "$1"
}

if [[ "$(uname -s)" == "Darwin" ]]; then
  # Flush DNS cache
  flush-dns() {
    sudo dscacheutil -flushcache
    sudo killall -HUP mDNSResponder
    echo "DNS cache flushed"
  }

  # Add SSH key to macOS keychain on shell start
  ssh-add --apple-use-keychain ~/.ssh/id_ed25519 2>/dev/null

  # Generate random MAC address (useful for wifi restrictions)
  get-new-mac() {
    echo "Generating new MAC address for en0..."
    sudo /System/Library/PrivateFrameworks/Apple80211.framework/Resources/airport -z && \
    sudo ifconfig en0 ether "a0$(openssl rand -hex 5 | sed 's/\(.\{2\}\)/:\1/g')" && \
    networksetup -detectnewhardware
    echo "New MAC address applied"
  }

  # Quick access to airport utility
  alias airport="/System/Library/PrivateFrameworks/Apple80211.framework/Versions/A/Resources/airport"
fi
