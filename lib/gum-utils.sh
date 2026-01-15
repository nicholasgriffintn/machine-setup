#!/bin/bash

HAS_GUM=false
if command -v gum &> /dev/null; then
    HAS_GUM=true
fi

log() {
    local level="${1:-info}"
    shift
    local message="$*"

    if $HAS_GUM; then
        case "$level" in
            success) gum style --foreground 2 "✓ $message" ;;
            warn)    gum style --foreground 3 "⚠ $message" ;;
            error)   gum style --foreground 196 "✗ $message" ;;
            info)    gum style --foreground 212 "$message" ;;
            header)  gum style --border rounded --padding "1 2" --margin "1" "$message" ;;
            *)       gum style "$message" ;;
        esac
    else
        case "$level" in
            success) echo "✓ $message" ;;
            warn)    echo "⚠ $message" ;;
            error)   echo "✗ $message" ;;
            header)  echo "=== $message ===" ;;
            *)       echo "$message" ;;
        esac
    fi
}

log_banner() {
    local border="${1:-double}"
    shift
    if $HAS_GUM; then
        gum style --border "$border" --padding "1 2" --margin "1" --foreground 212 "$@"
    else
        echo "=== $1 ==="
        shift
        for line in "$@"; do
            echo "$line"
        done
    fi
}

spin() {
    local title="$1"
    shift
    if $HAS_GUM; then
        gum spin --spinner dot --title "$title" -- "$@"
    else
        echo "$title"
        "$@"
    fi
}

confirm() {
    local prompt="$1"
    if $HAS_GUM; then
        gum confirm "$prompt"
    else
        read -p "$prompt (Y/N) " -n 1 -r
        echo
        [[ $REPLY =~ ^[Yy]$ ]]
    fi
}

input() {
    local prompt="$1"
    local default="${2:-}"
    local result

    if $HAS_GUM; then
        result=$(gum input --placeholder "$default" --prompt "$prompt " --value "$default")
        echo "${result:-$default}"
    else
        read -p "$prompt [$default]: " result
        echo "${result:-$default}"
    fi
}
