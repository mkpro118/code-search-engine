import dataclasses
import pathlib

from snippets.languages import Language


@dataclasses.dataclass
class Snippet:
    content: str
    language: Language

    @classmethod
    def from_file(cls, filepath: str | pathlib.Path) -> 'Snippet':
        if not isinstance(filepath, pathlib.Path):
            filepath = pathlib.Path(filepath).resolve()
        filepath.resolve()

        if not filepath.is_file():
            raise ValueError(
                f'{filepath} does not exist or is not a regular file'
            )

        try:
            language = Language.from_file_extension(filepath)
        except ValueError:
            raise ValueError(
                'Your file seems to be a language that is not yet supported'
            )

        with open(str(filepath)) as f:
            content = f.read()

        return cls(content=content, language=language)
