import enum
import pathlib


class Language(enum.Enum):
    C = 'The C Programming Language'
    CSS = 'Cascading Style Sheets'
    CSV = 'Comma Separated Values'
    HTML = 'Hyper Text Markup Language'
    JS = 'JavaScript'
    JSON = 'JavaScript Object Notation'
    JSX = 'JavaScript Extended'
    MD = 'Markdown'
    PY = 'Python'
    TXT = 'Plain Text'
    YAML = "Yaml Ain't Markup Language"

    @classmethod
    def from_file_extension(cls, filepath: str | pathlib.Path) -> 'Language':
        if not isinstance(filepath, pathlib.Path):
            filepath = pathlib.Path(filepath)

        ext = filepath.suffix

        # char at index 0 is the dot ('.'), must have something after that
        # to determine language.
        # Assert that there's at least 2 characters in the suffix
        if len(ext) < 2:
            raise ValueError(f'File {filepath} has no extension')

        # Ignore the dot
        ext = ext[1:]

        simple_set = set(
            ('css', 'csv', 'html', 'json', 'jsx', 'md', 'py', 'txt')
        )

        if ext in ('c', 'h'):
            return cls.C
        elif ext in simple_set:
            return cls[ext.upper()]
        elif ext in ('js', 'mjs'):
            return cls.JS
        elif ext in ('yaml', 'yml'):
            return cls.YAML

        raise ValueError('Unrecognized extension')
