from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET
import re

from indd2docx.model.document import (
    Border, CharacterFormat, Color, DocumentModel, ImageRef, Page,
    Paragraph, ParagraphFormat, Run, Story, Style, Table, TableCell,
    TableRow, TextFrame,
)


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def number(value: str | None, default: float | None = None) -> float | None:
    if value is None or not str(value).strip():
        return default
    try:
        return float(str(value).strip().replace("pt", ""))
    except ValueError:
        return default


def integer(value: str | None, default: int = 0) -> int:
    n = number(value)
    return default if n is None else int(n)


def boolean(value: str | None) -> bool:
    return str(value).lower() in {"true", "yes", "1"}


def ref_name(value: str | None) -> str | None:
    if not value:
        return None
    return value.split("/")[-1].replace("$ID/", "")


class IDMLParser:
    """Parse IDML into the renderer-neutral internal DocumentModel."""

    def __init__(self, package_root: Path):
        self.root = Path(package_root).resolve()
        self.styles: dict[str, Style] = {}
        self.colors: dict[str, Color] = {}
        self.pages: dict[str, Page] = {}
        self.frames: dict[str, TextFrame] = {}
        self.story_paths: dict[str, Path] = {}

    def parse(self, name: str | None = None) -> DocumentModel:
        designmap_path = self.root / "designmap.xml"
        if not designmap_path.is_file():
            raise FileNotFoundError(designmap_path)
        designmap = ET.parse(designmap_path).getroot()
        model = DocumentModel(name or self.root.name)
        self._parse_resources()
        self._index_stories()
        self._parse_spreads(designmap)
        for story_id in self._story_order(designmap):
            path = self.story_paths.get(story_id)
            if path is not None:
                model.stories.append(self._parse_story(story_id, path))
        model.pages = list(self.pages.values())
        model.styles = list(self.styles.values())
        model.images = [image for story in model.stories for image in story.images]
        return model

    def _parse_resources(self) -> None:
        styles_dir = self.root / "Resources" / "Styles"
        if styles_dir.exists():
            for path in sorted(styles_dir.rglob("*.xml")):
                try:
                    root = ET.parse(path).getroot()
                except ET.ParseError:
                    continue
                for element in root.iter():
                    tag = local_name(element.tag)
                    if tag not in {"ParagraphStyle", "CharacterStyle"}:
                        continue
                    sid = element.attrib.get("Self")
                    if not sid:
                        continue
                    self.styles[sid] = Style(
                        id=sid,
                        name=element.attrib.get("Name") or ref_name(sid) or sid,
                        kind="paragraph" if tag == "ParagraphStyle" else "character",
                        based_on=element.attrib.get("BasedOn"),
                        character=self._character_format(element.attrib),
                        paragraph=self._paragraph_format(element.attrib),
                    )
        for candidate in (self.root / "Resources" / "Swatches.xml", self.root / "Resources" / "Colors.xml"):
            if not candidate.exists():
                continue
            try:
                root = ET.parse(candidate).getroot()
            except ET.ParseError:
                continue
            for element in root.iter():
                sid = element.attrib.get("Self")
                if sid:
                    self.colors[sid] = self._color_from_element(element)

    def _color_from_element(self, element) -> Color:
        space = element.attrib.get("Space", "").lower()
        values = element.attrib.get("ColorValue", "")
        try:
            nums = tuple(float(x) for x in re.split(r"\s+", values.strip()) if x)
        except ValueError:
            nums = ()
        if "rgb" in space and len(nums) >= 3:
            return Color(rgb="%02X%02X%02X" % tuple(max(0, min(255, round(x))) for x in nums[:3]))
        if "cmyk" in space and len(nums) >= 4:
            return Color(cmyk=nums[:4])
        if "gray" in space and nums:
            return Color(gray=nums[0])
        return Color(name=element.attrib.get("Name") or element.attrib.get("Self"))

    def _index_stories(self) -> None:
        stories_dir = self.root / "Stories"
        if not stories_dir.exists():
            return
        for path in sorted(stories_dir.glob("*.xml")):
            match = re.search(r"Story_(.+)\.xml$", path.name)
            if match:
                self.story_paths[match.group(1)] = path

    def _story_order(self, designmap) -> list[str]:
        result = [x for x in designmap.attrib.get("StoryList", "").split() if x]
        for element in designmap.iter():
            if local_name(element.tag) != "Story":
                continue
            src = element.attrib.get("src")
            if src:
                match = re.search(r"Story_(.+)\.xml$", src)
                if match and match.group(1) not in result:
                    result.append(match.group(1))
        for story_id in self.story_paths:
            if story_id not in result:
                result.append(story_id)
        return result

    def _parse_spreads(self, designmap) -> None:
        for element in designmap.iter():
            if local_name(element.tag) != "Spread" or not element.attrib.get("src"):
                continue
            path = self.root / element.attrib["src"].lstrip("/")
            if not path.exists():
                continue
            try:
                root = ET.parse(path).getroot()
            except ET.ParseError:
                continue
            for node in root.iter():
                tag = local_name(node.tag)
                if tag == "Page":
                    pid = node.attrib.get("Self")
                    if not pid:
                        continue
                    bounds = self._bounds(node.attrib.get("GeometricBounds"))
                    width = height = None
                    if bounds:
                        top, left, bottom, right = bounds
                        width, height = abs(right-left), abs(bottom-top)
                    self.pages[pid] = Page(pid, node.attrib.get("Name"), width, height, node.attrib.get("AppliedMaster"))
                elif tag == "TextFrame":
                    tid = node.attrib.get("Self")
                    if tid:
                        self.frames[tid] = TextFrame(
                            tid, node.attrib.get("ParentStory"), node.attrib.get("ParentPage"),
                            self._bounds(node.attrib.get("GeometricBounds")),
                        )

    @staticmethod
    def _bounds(value: str | None):
        if not value:
            return None
        try:
            values = tuple(float(x) for x in value.split())
        except ValueError:
            return None
        return values if len(values) == 4 else None

    def _parse_story(self, story_id: str, path: Path) -> Story:
        root = ET.parse(path).getroot()
        story = Story(id=story_id, text_frames=[f for f in self.frames.values() if f.story_id == story_id])
        for child in list(root):
            tag = local_name(child.tag)
            if tag == "ParagraphStyleRange":
                story.paragraphs.append(self._parse_paragraph(child))
            elif tag == "Table":
                story.tables.append(self._parse_table(child))
            elif tag in {"Rectangle", "Image", "PDF", "EPS", "Graphic"}:
                image = self._parse_image(child)
                if image:
                    story.images.append(image)
        return story

    def _parse_paragraph(self, element) -> Paragraph:
        fmt = self._paragraph_format(element.attrib)
        fmt.paragraph_style = ref_name(element.attrib.get("AppliedParagraphStyle"))
        paragraph = Paragraph(format=fmt)
        for child in list(element):
            if local_name(child.tag) != "CharacterStyleRange":
                continue
            character = self._character_format(child.attrib)
            character.character_style = ref_name(child.attrib.get("AppliedCharacterStyle"))
            for node in child.iter():
                tag = local_name(node.tag)
                if tag == "Content":
                    paragraph.runs.append(Run(node.text or "", character=character))
                elif tag in {"Br", "Brk"}:
                    paragraph.runs.append(Run("\n", character=character))
        return paragraph

    def _parse_table(self, element) -> Table:
        table = Table(column_count=integer(element.attrib.get("ColumnCount")), style_name=ref_name(element.attrib.get("AppliedTableStyle")))
        row_index = 0
        for row_element in element.iter():
            if local_name(row_element.tag) != "Row":
                continue
            row = TableRow(row_index, number(row_element.attrib.get("Height")))
            column = 0
            for cell_element in list(row_element):
                if local_name(cell_element.tag) != "Cell":
                    continue
                cell = self._parse_cell(cell_element, row_index, column)
                row.cells.append(cell)
                column += max(1, cell.column_span)
            table.rows.append(row)
            row_index += 1
        if table.column_count == 0:
            table.column_count = max((sum(c.column_span for c in r.cells) for r in table.rows), default=0)
        return table

    def _parse_cell(self, element, row: int, column: int) -> TableCell:
        cell = TableCell(
            row=row, column=column,
            row_span=integer(element.attrib.get("RowSpan"), 1),
            column_span=integer(element.attrib.get("ColumnSpan"), 1),
            width_pt=number(element.attrib.get("Width")),
            height_pt=number(element.attrib.get("Height")),
            vertical_alignment=element.attrib.get("VerticalJustification"),
        )
        fill_name = element.attrib.get("FillColor")
        if fill_name:
            cell.fill = self.colors.get(fill_name) or Color(name=fill_name)
        for side in ("Top", "Right", "Bottom", "Left"):
            weight = number(element.attrib.get(f"{side}EdgeStrokeWeight"), 0.0) or 0.0
            color_name = element.attrib.get(f"{side}EdgeStrokeColor")
            visible = weight > 0 and color_name not in {None, "None", "$ID/[None]", "[None]"}
            color = self.colors.get(color_name) if color_name else None
            if color is None and color_name:
                color = Color(name=color_name)
            cell.borders[side.lower()] = Border(visible=visible, width_pt=weight, color=color, style=element.attrib.get(f"{side}EdgeStrokeType"))
        for child in list(element):
            if local_name(child.tag) == "ParagraphStyleRange":
                cell.paragraphs.append(self._parse_paragraph(child))
        return cell

    def _parse_image(self, element) -> ImageRef | None:
        uri = element.attrib.get("LinkResourceURI") or element.attrib.get("SourceFileURI") or element.attrib.get("Href") or element.attrib.get("Link")
        if not uri:
            return None
        bounds = self._bounds(element.attrib.get("GeometricBounds"))
        width = height = None
        if bounds:
            top, left, bottom, right = bounds
            width, height = abs(right-left), abs(bottom-top)
        return ImageRef(uri, width_pt=width, height_pt=height, anchored=bool(element.attrib.get("ParentStory")))

    @staticmethod
    def _character_format(attrs) -> CharacterFormat:
        font_style = attrs.get("FontStyle", "").lower()
        position = attrs.get("Position", "").lower()
        return CharacterFormat(
            font_family=attrs.get("AppliedFont"),
            font_size_pt=number(attrs.get("PointSize")),
            bold=("bold" in font_style) if "FontStyle" in attrs else None,
            italic=("italic" in font_style) if "FontStyle" in attrs else None,
            underline=boolean(attrs.get("Underline")) if "Underline" in attrs else None,
            strike=boolean(attrs.get("StrikeThru")) if "StrikeThru" in attrs else None,
            tracking=number(attrs.get("Tracking")),
            baseline_shift_pt=number(attrs.get("BaselineShift")),
            superscript="superscript" in position,
            subscript="subscript" in position,
            capitalization=attrs.get("Capitalization"),
        )

    @staticmethod
    def _paragraph_format(attrs) -> ParagraphFormat:
        numbering = (attrs.get("BulletsAndNumberingListType") or attrs.get("BulletsAndNumberingText") or "").lower()
        return ParagraphFormat(
            alignment=attrs.get("Justification") or attrs.get("Alignment"),
            left_indent_pt=number(attrs.get("LeftIndent")),
            right_indent_pt=number(attrs.get("RightIndent")),
            first_line_indent_pt=number(attrs.get("FirstLineIndent")),
            space_before_pt=number(attrs.get("SpaceBefore")),
            space_after_pt=number(attrs.get("SpaceAfter")),
            leading_pt=number(attrs.get("Leading")),
            keep_with_next=boolean(attrs.get("KeepWithNext")),
            keep_lines_together=boolean(attrs.get("KeepLinesTogether")),
            bullet=bool(numbering and "number" not in numbering),
            numbered="number" in numbering,
        )
