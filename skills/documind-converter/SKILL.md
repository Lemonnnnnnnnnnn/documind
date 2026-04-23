---
name: documind-converter
description: Use when user asks to convert docx to markdown, extract content from Word documents, or process .docx files
---

# Documind Converter

Use this skill when the user wants to convert `.docx` files to Markdown format.

## When to Trigger

- User asks to convert docx to markdown
- User wants to extract content from Word documents
- User needs to process .docx files for LLM/RAG workflows
- User wants to split docx by heading levels into markdown chunks

## How to Use

The `documind` CLI tool is available in this project. Basic usage:

```bash
# Convert with default settings (split mode, level 2)
documind convert <input.docx> --out-dir ./output

# Generate single file markdown (inline mode)
documind convert <input.docx> --out-dir ./output --mode inline

# Custom split level
documind convert <input.docx> --out-dir ./output --split-level 3
```

### Common Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--out-dir` | Output directory | `dist/<doc-stem>` |
| `--split-level` | Heading level for splitting | `2` |
| `--mode` | `split` or `inline` | `split` |
| `--assets-dir` | Export images directory name | `assets` |
| `--table-mode` | `auto`, `markdown`, or `html` | `auto` |
| `--overwrite` | Overwrite existing output | false |
| `--verbose` | Show detailed logs | false |

## Output Structure

**Split mode** (default):
- `index.md` - Main content with chunk references
- `summary.json` - Metadata and chunk information
- `assets/` - Extracted images
- Nested directories for each heading level

**Inline mode**:
- `index.md` - Single markdown file
- `assets/` - Extracted images

## Examples

```bash
# Quick conversion
documind convert example/sample.docx

# Inline mode for single file
documind convert document.docx --mode inline --out-dir ./output

# High granularity splitting
documind convert example/sample.docx --split-level 3 --verbose

# Force markdown tables
documind convert tables.docx --table-mode markdown
```
