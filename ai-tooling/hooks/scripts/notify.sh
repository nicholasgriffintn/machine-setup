#!/usr/bin/env bash
# Unified notification script
# Usage: notify.sh "message" "sound" "urgency"
# Example: notify.sh "Task completed" "Ping" "low"

MESSAGE="${1:-Notification}"
SOUND="${2:-Glass}"
URGENCY="${3:-normal}"

if command -v osascript &> /dev/null; then
    osascript -e "display notification \"$MESSAGE\" with title \"Claude Code\" sound name \"$SOUND\""
elif command -v notify-send &> /dev/null; then
    notify-send "Claude Code" "$MESSAGE" --urgency="$URGENCY"
elif command -v powershell.exe &> /dev/null; then
    powershell.exe -Command "
        [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
        [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
        \$template = '<toast><visual><binding template=\"ToastText02\"><text id=\"1\">Claude Code</text><text id=\"2\">$MESSAGE</text></binding></visual></toast>'
        \$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
        \$xml.LoadXml(\$template)
        \$toast = [Windows.UI.Notifications.ToastNotification]::new(\$xml)
        [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('Claude Code').Show(\$toast)
    " 2>/dev/null || true
fi

exit 0
