#!/usr/bin/env python3
"""
Applies the tracked VS Code baseline (vscode/settings.json) to every VS Code
install on this machine -- stable, Insiders, and any profile under each.

The theme/font drift this fixes has three causes, all handled here:

  1. Settings Sync merges stable and Insiders into one bucket, so whichever
     window was closed last wins. A tracked baseline re-asserted on demand
     beats arguing with the merge.
  2. Nothing previously pinned `workbench.colorTheme` or the font families,
     so a theme extension update or a `window.autoDetectColorScheme` flip
     silently reverted them to defaults.
  3. Settings only referenced a theme by ID -- if the extension providing it
     wasn't installed, VS Code fell back to Dark+ without saying so.

Keys *not* in the baseline are left untouched, so machine-local values (the
agent sandbox paths, per-machine tsdk overrides) survive a re-run.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BASELINE = REPO_ROOT / 'vscode' / 'settings.json'
EXTENSIONS = REPO_ROOT / 'vscode' / 'extensions.txt'

# Each flavour's user data dir, plus the CLI candidates to try in order.
# The bundled launcher is the fallback because `code`/`code-insiders` only
# reach PATH if you've run "Install 'code' command in PATH" from the palette,
# which a fresh machine won't have. Note Insiders' bundled binary is still
# called `code`, not `code-insiders`.
INSTALLS = [
    (
        Path.home() / 'Library/Application Support/Code/User',
        ['code', '/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code'],
    ),
    (
        Path.home() / 'Library/Application Support/Code - Insiders/User',
        ['code-insiders', '/Applications/Visual Studio Code - Insiders.app/Contents/Resources/app/bin/code'],
    ),
]

# Fonts the baseline references. Missing ones aren't fatal -- the font stacks
# all fall back -- but a silent fallback is exactly the drift being fixed.
REQUIRED_FONTS = ['BBC Reith Sans', 'FantasqueSansM Nerd Font Mono']


def strip_jsonc(text: str) -> str:
    """VS Code writes settings.json as JSONC. Drop comments and trailing
    commas so json.loads can read a file a human has edited in the UI."""
    out = []
    i, n = 0, len(text)
    in_string = False
    while i < n:
        ch = text[i]
        if in_string:
            out.append(ch)
            if ch == '\\' and i + 1 < n:
                out.append(text[i + 1])
                i += 2
                continue
            if ch == '"':
                in_string = False
            i += 1
            continue
        if ch == '"':
            in_string = True
            out.append(ch)
            i += 1
            continue
        if ch == '/' and i + 1 < n and text[i + 1] == '/':
            i = text.find('\n', i)
            if i == -1:
                break
            continue
        if ch == '/' and i + 1 < n and text[i + 1] == '*':
            end = text.find('*/', i + 2)
            i = n if end == -1 else end + 2
            continue
        out.append(ch)
        i += 1
    return re.sub(r',(\s*[}\]])', r'\1', ''.join(out))


def read_settings(path: Path) -> dict:
    if not path.is_file():
        return {}
    raw = path.read_text()
    if not raw.strip():
        return {}
    try:
        return json.loads(strip_jsonc(raw))
    except json.JSONDecodeError as exc:
        print(f"  ! {path} is not valid JSON ({exc}); leaving it alone", file=sys.stderr)
        raise


def settings_targets(user_dir: Path):
    """The default profile's settings.json, plus one per named profile --
    profiles each keep their own copy, which is how a themed default profile
    can still open a window looking untouched."""
    yield user_dir / 'settings.json'
    profiles = user_dir / 'profiles'
    if profiles.is_dir():
        for profile in sorted(profiles.iterdir()):
            if (profile / 'settings.json').is_file():
                yield profile / 'settings.json'


def apply_baseline(target: Path, baseline: dict, dry_run: bool) -> bool:
    try:
        current = read_settings(target)
    except json.JSONDecodeError:
        return False

    changed = {k: v for k, v in baseline.items() if current.get(k) != v}
    if not changed:
        print(f"  = {target} already matches baseline")
        return True

    for key in sorted(changed):
        print(f"  ~ {key}")

    if dry_run:
        print(f"  (dry run) {len(changed)} key(s) would change in {target}")
        return True

    if target.is_file():
        shutil.copy2(target, target.with_suffix('.json.bak'))

    merged = {**current, **baseline}
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(f'.{target.name}.tmp')
    tmp.write_text(json.dumps(merged, indent=2) + '\n')
    tmp.replace(target)
    print(f"  ✓ {target} ({len(changed)} key(s) updated, previous copy at {target.name}.bak)")
    return True


def wanted_extensions() -> list:
    if not EXTENSIONS.is_file():
        return []
    lines = (line.split('#', 1)[0].strip() for line in EXTENSIONS.read_text().splitlines())
    return [line for line in lines if line]


def resolve_cli(candidates: list):
    for candidate in candidates:
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
        if Path(candidate).is_file() and os.access(candidate, os.X_OK):
            return candidate
    return None


def sync_extensions(candidates: list, dry_run: bool) -> None:
    cli = resolve_cli(candidates)
    if cli is None:
        print(f"  ! no usable CLI found (tried {', '.join(candidates)}) -- skipping extensions")
        return

    installed = subprocess.run([cli, '--list-extensions'], capture_output=True, text=True)
    if installed.returncode != 0:
        print(f"  ! `{cli} --list-extensions` failed: {installed.stderr.strip()}")
        return

    have = {ext.lower() for ext in installed.stdout.split()}
    missing = [ext for ext in wanted_extensions() if ext.lower() not in have]
    if not missing:
        print("  = all tracked extensions already installed")
        return

    for ext in missing:
        if dry_run:
            print(f"  (dry run) would install {ext}")
            continue
        result = subprocess.run(
            [cli, '--install-extension', ext, '--force'],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            print(f"  ✓ installed {ext}")
            continue
        # The CLI reports install errors on stdout, not stderr.
        detail = next(
            (line for line in reversed((result.stdout + result.stderr).splitlines())
             if line.startswith('Error')),
            'unknown error',
        )
        print(f"  ! failed to install {ext}: {detail}")


def check_fonts() -> None:
    """A missing font is why a pinned font stack still renders as Menlo."""
    if shutil.which('system_profiler') is None:
        return
    result = subprocess.run(
        ['system_profiler', 'SPFontsDataType'], capture_output=True, text=True,
    )
    families = set(re.findall(r'Family: (.+)', result.stdout))
    for font in REQUIRED_FONTS:
        if font in families:
            print(f"  ✓ font available: {font}")
        else:
            print(f"  ! font missing: {font} -- VS Code will silently fall back")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true',
                        help='show what would change without writing anything')
    parser.add_argument('--skip-extensions', action='store_true',
                        help='only sync settings')
    args = parser.parse_args()

    baseline = json.loads(strip_jsonc(BASELINE.read_text()))

    found_any = False
    for user_dir, cli_candidates in INSTALLS:
        if not user_dir.is_dir():
            continue
        found_any = True
        print(f"\n{user_dir.parent.name}")
        for target in settings_targets(user_dir):
            apply_baseline(target, baseline, args.dry_run)
        if not args.skip_extensions:
            sync_extensions(cli_candidates, args.dry_run)

    if not found_any:
        print("No VS Code installs found -- nothing to do.")
        return 0

    print("\nFonts")
    check_fonts()

    print("\nSettings Sync note: if you have it enabled, VS Code may push these "
          "values back out or overwrite them from another machine. Re-run this "
          "script, or exclude 'settings' from sync, to keep this repo authoritative.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
