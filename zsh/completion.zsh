#
# Completion Configuration
#

# Case-insensitive completion
zstyle ':completion:*' matcher-list 'm:{a-z}={A-Za-z}'

# Menu selection
zstyle ':completion:*' menu select

# Group results by category
zstyle ':completion:*' group-name ''

# Add colors to completion
zstyle ':completion:*' list-colors "${(s.:.)LS_COLORS}"

# Better descriptions
zstyle ':completion:*:descriptions' format '%F{yellow}-- %d --%f'
zstyle ':completion:*:warnings' format '%F{red}-- no matches found --%f'
