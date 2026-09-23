import shutil

COMMANDS = {}


def command(name, help_text, requires_confirmation=False):
    """requires_confirmation=True: caller must include the word 'confirm'."""

    def deco(fn):
        fn.meta = {"help": help_text, "requires_confirmation": requires_confirmation}
        COMMANDS[name] = fn
        return fn

    return deco


@command("status", "disk usage of this machine")
def cmd_status(args):
    du = shutil.disk_usage("/")
    pct = du.used / du.total * 100
    return f"disk {du.used >> 30}/{du.total >> 30} GB used ({pct:.0f}%)"


@command("boom", "test command, trust me", requires_confirmation=True)
def cmd_boom(args):
    return "fired"


def run_command(text, sender=None):
    parts = text.strip().split()
    if not parts:
        return None
    name = parts[0].lower()
    if name == "help":
        return help_reply()
    fn = COMMANDS.get(name)
    if fn is None:
        return f"unknown command '{name}' (say 'help')"
    if fn.meta["requires_confirmation"] and "confirm" not in parts[1:]:
        return f"'{name}' requires confirmation, resend with 'confirm'"
    return fn(parts[1:])


def help_reply():
    lines = [f"{n}: {fn.meta['help']}" for n, fn in COMMANDS.items()]
    return "commands: " + ", ".join(lines)
