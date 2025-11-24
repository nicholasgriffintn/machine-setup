#
# Vi Mode with Enhancements
#

bindkey -v

# Fix backspace in vi mode
bindkey -v '^?' backward-delete-char

# Better vi mode bindings
bindkey '^R' history-incremental-search-backward
bindkey '^P' up-history
bindkey '^N' down-history

# jk to exit insert mode
bindkey -M viins 'jk' vi-cmd-mode

# Edit command in editor with 'v' in normal mode
autoload -Uz edit-command-line
zle -N edit-command-line
bindkey -M vicmd 'v' edit-command-line

# Change cursor shape based on vi mode
autoload -Uz zle-keymap-select zle-line-init

function zle-keymap-select {
  if [[ ${KEYMAP} == vicmd ]] || [[ $1 = 'block' ]]; then
    echo -ne '\e[1 q'  # Block cursor
  elif [[ ${KEYMAP} == main ]] || [[ ${KEYMAP} == viins ]] || [[ ${KEYMAP} = '' ]] || [[ $1 = 'beam' ]]; then
    echo -ne '\e[5 q'  # Beam cursor
  fi
}
zle -N zle-keymap-select

# Start with beam cursor
echo -ne '\e[5 q'

# Reset cursor on each prompt
function zle-line-init {
  echo -ne '\e[5 q'
}
zle -N zle-line-init

# History Substring Search (bind after plugins load)
bindkey '^[[A' history-substring-search-up
bindkey '^[[B' history-substring-search-down
bindkey -M vicmd 'k' history-substring-search-up
bindkey -M vicmd 'j' history-substring-search-down

# Magic Enter (bind last to ensure it's not overridden)
zle -N magic-enter
bindkey "^M" magic-enter
