#!/bin/bash
# Repairs symlinks left stale by a repo move instead of treating "is a
# symlink" as "is correct"; backs up (never deletes) real files found at a
# target instead of skipping them, since a silent skip is how this drifted.
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
REPO_ROOT=$(cd -- "$SCRIPT_DIR/../.." &> /dev/null && pwd)
AI_TOOLING_DIR="$REPO_ROOT/ai-tooling"

# shellcheck source=/dev/null
source "$REPO_ROOT/lib/gum-utils.sh"

AI_TOOLING_MAPPINGS=(
    "~/.config/opencode/command:commands"
    "~/.config/opencode/INSTRUCTIONS.md:INSTRUCTIONS.md"
    "~/.claude/agents:agents"
    "~/.claude/hooks:hooks"
    "~/.claude/commands:commands"
    "~/.claude/skills:skills"
    "~/.claude/CLAUDE.md:INSTRUCTIONS.md"
    "~/.codex/skills:skills"
    "~/.codex/AGENTS.md:INSTRUCTIONS.md"
    "~/.codex/hooks:hooks"
    "~/.codex/hooks.json:codex-hooks.json"
    "~/.copilot/agents:agents"
    "~/.copilot/skills:skills"
    "~/.copilot/copilot-instructions.md:INSTRUCTIONS.md"
    "~/.gemini/skills:skills"
    "~/.gemini/GEMINI.md:INSTRUCTIONS.md"
)

if [ ! -d "$AI_TOOLING_DIR" ]; then
    log warn "No ai-tooling/ directory at $AI_TOOLING_DIR, nothing to link"
    exit 0
fi

log info "Syncing AI tooling symlinks from $AI_TOOLING_DIR ..."

if [ "$(git -C "$REPO_ROOT" config --get core.hooksPath)" != ".githooks" ]; then
    git -C "$REPO_ROOT" config core.hooksPath .githooks
    log success "  Installed pre-commit secret scan (core.hooksPath -> .githooks)"
fi

for mapping in "${AI_TOOLING_MAPPINGS[@]}"; do
    IFS=':' read -r target_path src_name <<< "$mapping"
    src_path="$AI_TOOLING_DIR/$src_name"
    target="${target_path/#\~/$HOME}"
    target_dir=$(dirname "$target")
    target_name=$(basename "$target")

    if [ ! -e "$src_path" ]; then
        continue
    fi

    mkdir -p "$target_dir"

    if [ -L "$target" ]; then
        current_link=$(readlink "$target")
        if [ "$current_link" = "$src_path" ]; then
            log success "  $target_name already linked correctly"
        else
            rm "$target"
            ln -s "$src_path" "$target"
            log success "  $target_name relinked (was pointing to stale location: $current_link)"
        fi
    elif [ -e "$target" ]; then
        backup="$target.bak-$(date +%Y%m%d%H%M%S)"
        mv "$target" "$backup"
        ln -s "$src_path" "$target"
        log warn "  $target_name existed as a real file/dir, backed up to $backup and linked"
    else
        ln -s "$src_path" "$target"
        log success "  Linked $target_name -> $src_name"
    fi
done

python3 "$AI_TOOLING_DIR/scripts/render-claude-settings.py"

if [ -f "$HOME/.codex/config.toml" ]; then
    python3 "$AI_TOOLING_DIR/scripts/sync-codex-env.py"
fi

# Only install the refresher once the private key actually exists locally
# -- see check-bot-identity-configured.py for why presence in the
# git-tracked settings file alone isn't enough.
if python3 "$AI_TOOLING_DIR/scripts/check-bot-identity-configured.py"; then
    bash "$AI_TOOLING_DIR/scripts/install-gh-token-refresher.sh"
fi
