---
name: epub-chapter-extractor
description: Extract all chapters from an EPUB file into separate markdown files. Use when the user wants to split an EPUB into individual chapter files, extract EPUB chapters, or convert an ebook to separate markdown documents.
category: documents-and-data
metadata:
  version: "1.0"
  changelog:
    - "1.0: Promoted to trinity-skills library (2026-08-04)"
---

# EPUB Chapter Extractor

Extract each chapter from an EPUB file into its own markdown file.

## Requirements

- Python 3.8+
- `uv` package manager (recommended) OR pip

## Instructions

When the user wants to extract chapters from an EPUB, run the extraction script:

**Using uv (recommended):**
```bash
uv run --with ebooklib --with beautifulsoup4 --with html2text --with lxml python "$(dirname "$0")/extract_chapters.py" "/path/to/book.epub" [output_dir]
```

**Using pip (alternative):**
```bash
pip install ebooklib beautifulsoup4 html2text lxml
python "$(dirname "$0")/extract_chapters.py" "/path/to/book.epub" [output_dir]
```

If `output_dir` is omitted, creates a folder named after the EPUB in the same directory.

## Example

User: "Extract chapters from /Users/me/Books/mybook.epub"

```bash
cd ~/.claude/skills/epub-chapter-extractor && uv run --with ebooklib --with beautifulsoup4 --with html2text --with lxml python extract_chapters.py "/Users/me/Books/mybook.epub"
```

Output files will be at `/Users/me/Books/mybook/`:
- `01_introduction.md`
- `02_chapter_one.md`
- etc.

After extraction, open the output folder:

```bash
open /Users/me/Books/mybook
```

## Output Format

Each chapter file contains:

```markdown
# Chapter Title

[Chapter content in markdown format]
```

Files are numbered for proper sorting: `01_`, `02_`, etc.

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `uv not found` | uv package manager not installed | Run: `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| `EPUB has no chapters` | EPUB lacks proper table of contents | Script requires TOC entries; manually check EPUB structure |
| `File not found` | Invalid EPUB path | Verify file exists and path is correct |
| `Permission denied` | Can't write to output directory | Check write permissions on output folder |
| `Invalid EPUB format` | Corrupted or non-standard EPUB | Try a different EPUB reader to validate the file |
| `Module not found` | Dependencies not installed | Ensure ebooklib, beautifulsoup4, html2text, lxml are installed |
