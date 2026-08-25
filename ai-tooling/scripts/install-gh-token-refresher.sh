#!/bin/bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
LABEL="com.nicholasgriffin.machine-setup.refresh-gh-token"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
LOG_DIR="$HOME/Library/Logs/machine-setup"
PYTHON3="$(command -v python3)"
# launchd jobs get a minimal default environment -- refresh-gh-token.py and
# github-app-token.py shell out to bare `python3`/`openssl`/`git`, which
# would fail to resolve without this, independent of the absolute path used
# for the job's own program below.
JOB_PATH="/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

mkdir -p "$LOG_DIR"

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>$PYTHON3</string>
    <string>$SCRIPT_DIR/refresh-gh-token.py</string>
  </array>
  <key>StartInterval</key>
  <integer>1800</integer>
  <key>RunAtLoad</key>
  <true/>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key>
    <string>$JOB_PATH</string>
  </dict>
  <key>StandardOutPath</key>
  <string>$LOG_DIR/refresh-gh-token.log</string>
  <key>StandardErrorPath</key>
  <string>$LOG_DIR/refresh-gh-token.log</string>
</dict>
</plist>
EOF

launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"
echo "Installed and loaded $LABEL (refreshes GH_TOKEN every 30 min)"
