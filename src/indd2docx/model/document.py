from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Color:
    rgb: str | None = None
    cmyk: tuple[float, float, float, float] | None = None
    gray: float | None = None
    name: str | None = None
    tint: float = 100.0


@dataclass(frozen=True)
class Border:
    visible: bool = False
    width_pt: float = 0.0
    color: Color | None = None
    style: str | None = None


@dataclass
class CharacterFormat:
    font_family: str | None = None
    font_size_pt: float | None = None
    bold: bool | None = None
    italic: bool | None = None
    underline: bool | None = None
    strike: bool | None = None
    color: Color | None = None
    tracking: float | None = None
    baseline_shift_pt: float | None = None
    superscript: bool = False
    subscript: bool = False
    capitalization: str | None = None
    character_style: str | None = None


@dataclass
class ParagraphFormat:
    alignment: str | None = None
    left_indent_pt: float | None = None
    right_indent_pt: float | None = None
    first_line_indent_pt: float | None = None
    space_before_pt: float | None = None
    space_after_pt: float | None = None
    leading_pt: float | None = None
    keep_with_next: bool = False
    keep_lines_together: bool = False
    bullet: bool = False
    numbered: bool = False
    paragraph_style: str | None = None


@dataclass
class Run:
    text: str
    character: CharacterFormat = field(default_factory=CharacterFormat)
    hyperlink: str | None = None


@dataclass
class Paragraph:
    runs: list[Run] = field(default_factory=list)
    format: ParagraphFormat = field(default_factory=ParagraphFormat)

    @property
    def text(self) -> str:
        return "".join(run.text for run in self.runs)


@dataclass
class ImageRef:
    resource_uri: str
    path: str | None = None
    width_pt: float | None = None
    height_pt: float | None = None
    rotation: float = 0.0
    anchored: bool = False


@dataclass
class TableCell:
    row: int
    column: int
    row_span: int = 1
    column_span: int = 1
    width_pt: float | None = None
    height_pt: float | None = None
    vertical_alignment: str | None = None
    fill: Color | None = None
    borders: dict[str, Border] = field(default_factory=dict)
    paragraphs: list[Paragraph] = field(default_factory=list)


@dataclass
class TableRow:
    index: int
    height_pt: float | None = None
    cells: list[TableCell] = field(default_factory=list)


@dataclass
class Table:
    rows: list[TableRow] = field(default_factory=list)
    column_count: int = 0
    style_name: str | None = None


@dataclass
class TextFrame:
    id: str
    story_id: str | None = None
    page_id: str | None = None
    geometric_bounds: tuple[float, float, float, float] | None = None


@dataclass
class Story:
    id: str
    paragraphs: list[Paragraph] = field(default_factory=list)
    tables: list[Table] = field(default_factory=list)
    images: list[ImageRef] = field(default_factory=list)
    text_frames: list[TextFrame] = field(default_factory=list)

    @property
    def text(self) -> str:
        parts = [p.text for p in self.paragraphs]
        for table in self.tables:
            for row in table.rows:
                for cell in row.cells:
                    parts.extend(p.text for p in cell.paragraphs)
        return "\n".join(parts)


@dataclass
class Page:
    id: str
    name: str | None = None
    width_pt: float | None = None
    height_pt: float | None = None
    applied_master: str | None = None


@dataclass
class Section:
    start_page_id: str | None = None
    page_number_start: int | None = None


@dataclass
class Style:
    id: str
    name: str
    kind: str
    based_on: str | None = None
    character: CharacterFormat = field(default_factory=CharacterFormat)
    paragraph: ParagraphFormat = field(default_factory=ParagraphFormat)


@dataclass
class DocumentModel:
    name: str
    pages: list[Page] = field(default_factory=list)
    sections: list[Section] = field(default_factory=list)
    stories: list[Story] = field(default_factory=list)
    styles: list[Style] = field(default_factory=list)
    images: list[ImageRef] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "\n".join(story.text for story in self.stories)

    @property
    def paragraph_count(self) -> int:
        return sum(len(s.paragraphs) for s in self.stories) + sum(
            len(c.paragraphs)
            for s in self.stories for t in s.tables for r in t.rows for c in r.cells
        )

    @property
    def table_count(self) -> int:
        return sum(len(s.tables) for s in self.stories)
