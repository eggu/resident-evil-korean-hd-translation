"""Build against the caller's original files; never guess the installed game path."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def required_directory(name):
    value = os.environ.get(name)
    if not value:
        raise ValueError(f'Set {name} to the original input directory; see README.md')
    path = Path(value).expanduser().resolve()
    if not path.is_dir():
        raise ValueError(f'{name} directory does not exist: {path}')
    return path


GAME = required_directory('RE1_GAME_ORIGINAL_DIR')
default_font = (Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts/batang.ttc'
                if os.name == 'nt' else Path('/System/Library/Fonts/Supplemental/AppleMyungjo.ttf'))
FONT = Path(os.environ.get('RE1_BUILD_FONT', default_font)).expanduser().resolve()
if not FONT.is_file():
    raise ValueError('Set RE1_BUILD_FONT to a Korean TTF/OTF/TTC font file; see README.md')
