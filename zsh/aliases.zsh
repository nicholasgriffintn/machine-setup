#
# Aliases
#

# Safety
alias rm='rm -i'
alias cp='cp -i'
alias mv='mv -i'

# Global Aliases
alias -g G='| grep'
alias -g L='| less'
alias -g C='| pbcopy'

# Suffix Aliases
alias -s {json,md,txt,yaml,yml}=$EDITOR
alias -s {html,js,ts,css}=code

# Clipboard
alias cpath='pwd | pbcopy'
alias cfile='pbcopy <'

# Directory listing (with eza if available)
if command -v eza &>/dev/null; then
  alias ls='eza --icons --group-directories-first'
  alias ll='eza -lah --icons --git --group-directories-first'
  alias la='eza -A --icons --group-directories-first'
  alias lt='eza --tree --level=2 --icons'
  alias l='eza -F --icons'
else
  alias ls='ls -G'
  alias ll='ls -lah'
  alias la='ls -A'
  alias l='ls -CF'
  # Fallback tree alias when eza not available
  if command -v tree &>/dev/null; then
    alias lt='tree -L 2'
  fi
fi

# Better cat with bat
if command -v bat &>/dev/null; then
  alias cat='bat --style=auto'
  alias catt='/bin/cat'  # Keep original cat available
  export MANPAGER="sh -c 'col -bx | bat -l man -p'"
fi

# Better git diff with delta
if command -v delta &>/dev/null; then
  export GIT_PAGER='delta'
fi

# Directory navigation
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'
alias -- -='cd -'
alias dirs='dirs -v'  # Show directory stack

# Directory hashing for quick navigation
hash -d workspace=~/workspace
hash -d github=~/Documents/GitHub
hash -d setup=~/Documents/GitHub/machine-setup

# Git shortcuts
alias gs='git status'
alias ga='git add'
alias gc='git commit'
alias gp='git pull'
alias gph='git push'
alias gco='git checkout'
alias gd='git diff'
alias gl='git log --oneline --graph --decorate'
alias gb='git branch'

# Docker shortcuts
alias d='docker'
alias dc='docker-compose'
alias dps='docker ps'
alias dimg='docker images'
alias dclean='docker system prune -af --volumes'
alias dstop='docker stop $(docker ps -aq)'
alias drm='docker rm $(docker ps -aq)'
alias dlogs='docker logs -f'
alias dexec='docker exec -it'

# Kubernetes (if installed)
if command -v kubectl &>/dev/null; then
  alias k='kubectl'
  alias kgp='kubectl get pods'
  alias kgs='kubectl get services'
  alias kgd='kubectl get deployments'
fi

# Terraform (if installed)
if command -v terraform &>/dev/null; then
  alias tf='terraform'
  alias tfi='terraform init'
  alias tfp='terraform plan'
  alias tfa='terraform apply'
fi

# Python
alias py='python3'
alias pip='pip3'

# Neovim
if command -v nvim &>/dev/null; then
  alias vim='nvim'
  alias vi='nvim'
fi

# Development shortcuts
# Smart serve - uses soft-serve for git repos, python server for others
if command -v soft &>/dev/null; then
  alias serve='smart-serve'
else
  alias serve='python3 -m http.server'
fi

# Quick npm/pnpm shortcuts
alias ni='npm install'
alias nid='npm install --save-dev'
alias nr='npm run'
alias nrs='npm run start'
alias nrd='npm run dev'
alias nrb='npm run build'
alias nrt='npm run test'

# pnpm equivalents
alias pi='pnpm install'
alias pid='pnpm install --save-dev'
alias pr='pnpm run'
alias prd='pnpm run dev'
alias prb='pnpm run build'
alias prt='pnpm run test'

# Quick edit
alias zshrc='$EDITOR ~/.zshrc'
alias reload='source ~/.zshrc'

# Tmux
if command -v tmux &>/dev/null; then
  alias ta='tmux attach -t'
  alias tl='tmux list-sessions'
  alias tn='tmux new-session -s'
  alias tk='tmux kill-session -t'
fi

if command -v lazygit &>/dev/null; then
  alias lg='lazygit'
fi

# System monitoring - prefer btop, fallback to htop
if command -v btop &>/dev/null; then
  alias top='btop'
elif command -v htop &>/dev/null; then
  alias top='htop'
fi

if command -v tlrc &>/dev/null; then
  alias help='tlrc'
  alias tldr='tlrc'
fi

if command -v http &>/dev/null; then
  alias get='http GET'
  alias post='http POST'
  alias put='http PUT'
  alias delete='http DELETE'
fi

# Better man pages with tldr
man() {
  if command -v tlrc &>/dev/null; then
    tlrc "$1" 2>/dev/null || command man "$1"
  else
    command man "$1"
  fi
}
