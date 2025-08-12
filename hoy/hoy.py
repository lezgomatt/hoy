import os
import platform
import re
import subprocess
import sys
import tomllib
import typing as t


__version__ = "1.0.6"


def main() -> None:
    system = determine_system()

    try:
        with open(f"{system.get_config_dir()}/hoy.toml", "rb") as config_file:
            config = tomllib.load(config_file)
    except FileNotFoundError:
        config = {}

    channels, args = extract_channels(sys.argv[1:])
    if not channels:
        channels = config.get("default_channels") or ["default"]

    for ch in channels:
        ch_config = config.get("channels", {}).get(ch, {})
        title = ch_config.get("title", "Hoy!")
        default_message = ch_config.get("default_message", "Task completed.")
        success_message = ch_config.get("success_message", "Task completed successfully.")
        failure_message = ch_config.get("failure_message", "Task failed.")

        message = " ".join(args) if len(args) > 0 else default_message
        try:
            message = success_message if int(message) == 0 else failure_message
        except ValueError:
            pass

        type = ch_config.get("type", "system")
        if type == "system":
            sound_name = ch_config.get("sound_name")
            system.show_notification(title, message, sound_name)
        else:
            raise Exception(f"Unsupported channel type: {type}")


def extract_channels(args: list[str]) -> tuple[list[str], list[str]]:
    """Zero or more channels can be specified at the start or end, but not in the middle."""

    channels = []

    for arg in args:
        if (m := re.match(r"@([A-Za-z0-9_\-]+)", arg)) is not None:
            channels.append(m[1])
        else:
            break

    remaining_args = args[len(channels):]

    while len(args) > 0 and (m := re.match(r"@([A-Za-z0-9_\-]+)", args[-1])) is not None:
        args.pop()
        channels.append(m[1])

    return channels, remaining_args


def determine_system() -> "SupportedSystem":
    system_id = platform.system()
    if system_id == MacOS.SYSTEM_ID:
        return MacOS()
    elif system_id == Linux.SYSTEM_ID:
        return Linux()
    elif system_id == Windows.SYSTEM_ID:
        return Windows()
    else:
        raise Exception(f"Unsupported system: {system_id}")


class SupportedSystem(t.Protocol):
    def get_config_dir(self) -> str:
        ...

    def show_notification(self, title: str, message: str, sound_name: str|None = None) -> None:
        ...


class MacOS(SupportedSystem):
    SYSTEM_ID = "Darwin"

    def get_config_dir(self) -> str:
        return os.path.expanduser("~/Library/Application Support/hoy")

    def show_notification(self, title: str, message: str, sound_name: str|None = None) -> None:
        # https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/DisplayNotifications.html
        # Escaping: \ -> \\, " -> \"
        message = message.replace("\\", "\\\\").replace('"', '\\"')
        script = " ".join([
            f'display notification "{message}"',
            f'with title "{title}"',
            f'sound name "{sound_name or "Hero"}"',
        ])
        subprocess.run(["osascript", "-e", script], check=True, stdout=subprocess.DEVNULL)


class Linux(SupportedSystem):
    SYSTEM_ID = "Linux"

    def get_config_dir(self) -> str:
        config_home = os.getenv("XDG_CONFIG_HOME", "~/.config/")

        return os.path.expanduser(f"{config_home}/hoy")

    def show_notification(self, title: str, message: str, sound_name: str|None = None) -> None:
        # https://specifications.freedesktop.org/notification-spec/1.3/protocol.html#command-notify
        subprocess.run([
            "gdbus", "call", "--session",
            "--dest", "org.freedesktop.Notifications",
            "--object-path", "/org/freedesktop/Notifications",
            "--method", "org.freedesktop.Notifications.Notify",
            "hoy", # app_name
            "0", # replaces_id
            "dialog-information", # app_icon
            title, # summary
            message, # body
            "[]", # actions
            f"{'sound-name': <'{sound_name or "message"}'>}", # hints
            "5000", # expire_timeout
        ], check=True, stdout=subprocess.DEVNULL)


class Windows(SupportedSystem):
    SYSTEM_ID = "Windows"

    def get_config_dir(self) -> str:
        return os.path.expandvars(r"%APPDATA%\hoy")

    def show_notification(self, title: str, message: str, sound_name: str|None = None) -> None:
        # https://learn.microsoft.com/en-us/dotnet/api/system.windows.forms.notifyicon
        # Escaping: ' -> '' (two single quotes)
        message = message.replace("'", "''")
        command = " ".join([
            "[void] [System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms');",
            "$n = New-Object System.Windows.Forms.NotifyIcon;",
            f"$n.BalloonTipTitle = '{title}';",
            f"$n.BalloonTipText = '{message}'; ",
            "$n.Icon = [System.Drawing.SystemIcons]::Information;",
            "$n.BalloonTipIcon = 'Info';",
            "$n.Visible = $true;",
            "$n.ShowBalloonTip(5000);",
        ])
        subprocess.run(["powershell", "-Command", command], check=True, stdout=subprocess.DEVNULL)


if __name__ == "__main__":
    main()
