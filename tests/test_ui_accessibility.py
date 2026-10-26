from html.parser import HTMLParser
from pathlib import Path


class _UIParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.lang: str | None = None
        self.form_controls = 0
        self.labels = 0
        self.buttons = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "html":
            self.lang = attributes.get("lang")
        if tag in {"input", "select", "textarea"}:
            self.form_controls += 1
        if tag == "label":
            self.labels += 1
        if tag == "button":
            self.buttons += 1


def test_ui_has_language_labels_and_interactive_controls() -> None:
    parser = _UIParser()
    parser.feed((Path("ui") / "index.html").read_text(encoding="utf-8"))
    assert parser.lang == "en"
    assert parser.form_controls > 0
    assert parser.labels >= parser.form_controls
    assert parser.buttons >= 5
