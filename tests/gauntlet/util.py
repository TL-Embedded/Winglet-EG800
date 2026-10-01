from typing import TypeVar

T = TypeVar("T")

def format_value(value) -> str:
    if value is None:
        return ""
    if type(value) is str:
        return f'"{value}"'
    elif type(value) is bool:
        return "OK" if value else "ERROR"
    elif isinstance(value, Exception):
        if type(value) is StepError:
            return value.text
        return type(value).__name__
    return str(value)


def console_color(text: str, code: str) -> str:
    if code == 'w':
        return text

    return {
        "rb": "\033[41m",
        "gb": "\033[42m",
        "yb": "\033[43m",
        "r": "\033[31m",
        "g": "\033[32m",
        "y": "\033[33m",
        "b": "\033[34m",
        "m": "\033[35m",
        "c": "\033[36m",
        "f": "\033[2m",
    }[code] + text + "\033[0m"


class StepError(Exception):
    def __init__(self, text: str):
        self.text = text