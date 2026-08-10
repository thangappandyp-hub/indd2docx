# IDML → Internal Document Model

The parser is intentionally independent of DOCX generation.

## Source of truth

`designmap.xml` establishes the package-level story/spread references. Story XML is consumed in the order declared by `StoryList` when available. Remaining stories are appended deterministically by filename so content is not silently lost.

## Current model

- `DocumentModel`: document-wide pages, sections, stories, styles, images
- `Story`: paragraphs, tables, images, text frames
- `Paragraph`: paragraph formatting plus character runs
- `Run`: text plus character formatting and future hyperlink metadata
- `Table` / `TableRow` / `TableCell`: dimensions, spans, fills and four source border sides
- `Page`: page identity, size and master reference
- `TextFrame`: story/page relationship and geometric bounds
- `Style`: paragraph or character style definition

## Critical table-border rule

The parser records the source border state instead of inventing a Word border. A side is considered visible only when its source stroke weight is greater than zero and its source color is not an explicit `None` value. The DOCX renderer will consume this state later and emit explicit `w:val="nil"` for absent borders.

## Next extensions

The parser will be expanded using real InDesign-generated IDML fixtures for:

- full paragraph style inheritance
- character style inheritance
- swatches/tints and CMYK conversion
- table/cell styles
- row/column geometry
- linked resources and graphics
- threaded stories and frame order
- lists and numbering
- hyperlinks
- headers/footers and sections
