import platform
import subprocess
import sys


__version__ = "1.0.2"


def main() -> None:
    title = "Hoy!"
    message = sys.argv[1] if len(sys.argv) > 1 else "Task completed"

    system = platform.system()
    if system == "Darwin":
        # https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/DisplayNotifications.html
        # Escaping: \ -> \\, " -> \"
        message = message.replace("\\", "\\\\").replace('"', '\\"')
        script = " ".join([
            f'display notification "{message}"',
            f'with title "{title}"',
            'sound name "Hero"',
        ])
        subprocess.run(["osascript", "-e", script], check=True, stdout=subprocess.DEVNULL)
    elif system == "Linux":
        # https://specifications.freedesktop.org/notification-spec/1.3/protocol.html#command-notify
        subprocess.run([
            "gdbus", "call", "--session",
            "--dest", "org.freedesktop.Notifications",
            "--object-path", "/org/freedesktop/Notifications",
            "--method", "org.freedesktop.Notifications.Notify",
            "hoy",
            "0", # replaces_id
            "dialog-information",
            title, # summary
            message, # body
            "[]", # actions
            "{'sound-name': <'message'>}", # hints
            "5000", # expire_timeout
        ], check=True, stdout=subprocess.DEVNULL)
    elif system == "Windows":
        # https://learn.microsoft.com/en-us/dotnet/api/system.windows.forms.notifyicon
        # Escaping: ' -> '' (two single quotes)
        message = message.replace("'", "''")
        command = " ".join([
            "[void] [System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms');",
            "$n = New-Object System.Windows.Forms.NotifyIcon;",
            f"$n.BalloonTipTitle = '{title}';",
            f"$n.BalloonTipText = '{message}'; ",
            "$n.Icon = [System.Drawing.SystemIcons]::Information;",
            "$n.BalloonTipIcon = 'Info';", # Or 'None'
            "$n.Visible = $true;",
            "$n.ShowBalloonTip(5000);",
        ])
        subprocess.run(["powershell", "-Command", command], check=True, stdout=subprocess.DEVNULL)
    else:
        raise Exception(f"Unknown OS: {system}")


if __name__ == "__main__":
    main()
