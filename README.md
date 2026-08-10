# INDD2DOCX

Production pipeline for converting Adobe InDesign documents to editable Microsoft Word documents:

**INDD → IDML → Internal Document Model → DOCX → Validation → Conversion Report**

## Core requirements

- Use Adobe InDesign's supported IDML export mechanism.
- Never reverse-engineer the proprietary INDD binary format.
- Never use RTF or HTML as an intermediate representation.
- Keep IDML parsing independent from DOCX rendering.
- Preserve semantic reading order, text formatting, styles, tables, images, and page information as far as Word permits.
- Treat table borders explicitly: a borderless InDesign cell must not acquire a visible Word border.

## Development phases

1. INDD → IDML export and IDML package validation
2. IDML parser and independent document model
3. Text, paragraph and character styles
4. Tables, including strict border preservation
5. Images and graphics
6. Pages, sections, headers and footers
7. Lists, hyperlinks and advanced formatting
8. DOCX validation and conversion reports
9. Real-document regression corpus

## Phase 1

This branch establishes the project architecture and testing foundation. The next implementation step is the Adobe InDesign automation and IDML package reader.

## Platform

The INDD → IDML step requires Windows and Adobe InDesign. The later IDML → DOCX stages are designed to be independently testable.
