---
name: document-extractor
description: Extracts key information from documents (PDFs, images, text files) in a folder and creates structured markdown summaries with the same filename but .md extension. Use when you need to analyze and extract insights from multiple documents in a directory.
allowed-tools: Read, Write, Bash, Glob
category: documents-and-data
metadata:
  version: "1.0"
  changelog:
    - "1.0: Promoted to trinity-skills library (2026-08-04)"
---

# Document Extractor

Analyze documents in a specified folder and create structured markdown extracts that capture the most important information from each document.

## Workflow

### 1. Initial Setup
- Get current date/time: `date '+%Y-%m-%d %H:%M:%S %Z'`
- List all files in the specified folder
- Create output directory: `Files/[folder_name]/` in the workspace

### 2. Document Processing

For each document:
1. Read using the Read tool
2. Collect metadata (file hash, modification date, extraction timestamp)
3. Identify document type and extract key information
4. Write to `Files/[folder_name]/[original_name].md`

### 3. Information Categories

**Legal/Official Documents:** Document type/number, dates, issuing authority, key terms, obligations, deadlines

**Financial Documents:** Account numbers (masked), transactions, amounts, payment dates, tax info

**Insurance Documents:** Policy numbers, coverage types/limits, premiums, deductibles, exclusions

**Contracts/Agreements:** Party names, duration, obligations, payment terms, termination clauses

**Personal Documents:** Document numbers (masked), validity periods, restrictions

### 4. Output Template

```markdown
# [Document Title/Type]

## Document Information
- **Document Type**: [Type]
- **File Name**: [Original filename]
- **File Hash**: [MD5/SHA256 hash]
- **Last Modified**: [File modification date]
- **Extraction Date**: [Current timestamp]

## Key Information
[Main extracted data organized by relevance]

## Important Dates
- **Issue Date**: [Date]
- **Expiry Date**: [Date if applicable]
- **Next Action Required**: [Date/Description if applicable]

## Notes and Observations
- [Important observations]
- [Unusual clauses]
- [Action items]

---
*Extracted: [timestamp] | Original: [path]*
```

### 5. Security
- Mask sensitive info (show last 4 digits only)
- Note when information has been redacted
- Flag potential security concerns

### 6. Summary Report
After processing all documents, create `Files/[folder_name]/summary.md` with:
- Total documents processed
- Document categories found
- Key findings
- Items requiring attention

## Useful Commands

```bash
# Get timestamp
date '+%Y-%m-%d %H:%M:%S %Z'

# Get file hash (macOS)
md5 -q /path/to/file
shasum -a 256 /path/to/file | cut -d' ' -f1

# Get modification date (macOS)
stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" /path/to/file

# List documents
find /path/to/folder -type f \( -name "*.pdf" -o -name "*.txt" -o -name "*.jpg" -o -name "*.png" \)
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| File unreadable | Corrupted or encrypted file | Skip file, note in summary, try alternative viewer |
| PDF extraction fails | Scanned image PDF | Use OCR or note as "image-based PDF" |
| Output folder not writable | Permission issue | Check permissions on Files/ directory |
| Sensitive data detected | PII or credentials visible | Mask appropriately, flag for review |
| Duplicate files | Same content, different names | Note duplicates in summary, extract once |
| Unknown file type | Unsupported format | Skip with note, or convert to supported format first |
