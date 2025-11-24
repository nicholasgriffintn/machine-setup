#
# Environment Variables
#
export KEYTIMEOUT=1
export ZSH_TMUX_FIXTERM=true
export WORKSPACE_DIR=~/workspace

# Locale
export LANG=en_GB.UTF-8
export LC_ALL=en_GB.UTF-8

# Editor
export EDITOR=vim
export VISUAL="$EDITOR"

# Pager
export LESS='-R -M -i -j5'
export PAGER='less'

# Homebrew
export HOMEBREW_NO_AUTO_UPDATE=1

# Fix GPG https://github.com/keybase/keybase-issues/issues/2798
export GPG_TTY=$(tty)

# Colored Man Pages
export LESS_TERMCAP_mb=$'\e[1;32m'
export LESS_TERMCAP_md=$'\e[1;32m'
export LESS_TERMCAP_me=$'\e[0m'
export LESS_TERMCAP_se=$'\e[0m'
export LESS_TERMCAP_so=$'\e[01;33m'
export LESS_TERMCAP_ue=$'\e[0m'
export LESS_TERMCAP_us=$'\e[1;4;31m'

# Fix for docker plugin completion error
export ZSH_CACHE_DIR="$HOME/.cache/zsh"
[[ ! -d "$ZSH_CACHE_DIR/completions" ]] && mkdir -p "$ZSH_CACHE_DIR/completions"

# Style Zsh Autosuggestions
export ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE='fg=60'

# Enable async prompt updates for better performance
export POSH_GIT_ENABLED=true
