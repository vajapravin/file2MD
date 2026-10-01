"""JSON to Markdown converter using structured formatting and MarkItDown."""

import json
from pathlib import Path
from file2md.converters.base import BaseConverter


class JsonConverter(BaseConverter):
    """Converts JSON documents to readable syntax-highlighted Markdown code blocks."""

    def convert(self, file_path: Path) -> str:
        text = file_path.read_text(encoding="utf-8")
        try:
            parsed = json.loads(text)
            formatted_json = json.dumps(parsed, indent=2, ensure_ascii=False)
            return f"```json\n{formatted_json}\n```"
        except json.JSONDecodeError as exc:
            raise ValueError(f"Malformed JSON document: {exc.msg}") from exc
