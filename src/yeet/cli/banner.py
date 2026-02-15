"""ASCII art banner for yeet CLI."""

import random

import click
import pyfiglet

# Curated list of fonts that look good with "yeet"
BANNER_FONTS = [
    "slant",
    "small",
    "smslant",
    "standard",
    "big",
    "doom",
    "banner",
    "block",
    "lean",
    "mini",
    "script",
    "shadow",
    "speed",
    "starwars",
    "stop",
    "thick",
]


def print_banner() -> None:
    """Print a random ASCII art banner."""
    font = random.choice(BANNER_FONTS)
    try:
        banner = pyfiglet.figlet_format("yeet", font=font)
        click.echo(click.style(banner.rstrip(), fg="magenta"))
    except Exception:
        # Fallback if font fails
        click.echo(click.style("🚀 yeet", fg="magenta", bold=True))
