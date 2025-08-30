import re

def colorize(text, color_code):
    """Applies an ANSI color to the text for terminal output."""
    return f"{color_code}{text}\033[0m"

def strip_ansi_codes(text):
    """Removes ANSI escape sequences (for colors) from a string for web UI output."""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)