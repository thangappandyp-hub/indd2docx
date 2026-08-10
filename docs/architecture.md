# Architecture

```text
INDD
  |
  v
InDesignExporter
  |
  v
IDML package
  |
  v
IDMLPackageReader / Validator
  |
  v
IDML XML Parser
  |
  v
Independent Document Model
  |
  v
DOCX Renderer
  |
  v
DOCX Validator
  |
  v
Conversion Report
```

## Design rules

- INDD is never parsed as a proprietary binary format.
- IDML is the source of truth for document structure.
- Parsing is independent from rendering.
- The internal model must not depend on `python-docx`.
- Reading order follows InDesign story/thread information where available, not a simple global X/Y sort.
- Word's `Table Grid` style is not used as a substitute for source table borders.
- Every generated table cell will receive explicit border state; absent source strokes become `w:val="nil"`.
