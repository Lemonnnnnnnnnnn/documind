# documind

`documind` is a local CLI that converts `.docx` files into Markdown collections designed for LLM, RAG, and document-processing workflows. It extracts headings, paragraphs, images, and tables, then renders either a chunked Markdown tree or a single inline Markdown file.

[中文说明](README_CN.md)

## Features

- Convert `.docx` documents into Markdown optimized for downstream AI workflows.
- Split output by heading level into nested chunk directories.
- Export embedded media into `assets/` with rewritten relative paths.
- Preserve external hyperlinks and common inline styles.
- Render simple tables as Markdown and fall back to HTML for complex merged tables.
- Emit either split output plus `summary.json`, or a single `index.md` in inline mode.

## Install

### Binary install for macOS arm64

```bash
curl -fsSL https://raw.githubusercontent.com/crow/documind/main/install.sh | sh
```

The installer downloads the latest macOS arm64 binary from GitHub Releases into `~/.local/bin/documind`.

Verify the install:

```bash
documind --help
```

If `~/.local/bin` is not on your `PATH` yet:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

### Source install

Requirements:

- Python `>=3.11`
- `uv`

Install the project and development dependencies:

```bash
uv sync --extra dev
```

Run the CLI from the repository:

```bash
uv run documind --help
```

## Quick Start

Convert the public sample document into chunked Markdown:

```bash
uv run documind convert example/sample.docx --out-dir ./output --split-level 2
```

Generate a single inline Markdown file:

```bash
uv run documind convert example/sample.docx --out-dir ./output-inline --mode inline
```

Common options:

- `--out-dir`: output directory. Default: `dist/<doc-stem>`
- `--split-level`: heading level used for chunk splitting. Default: `2`
- `--assets-dir`: exported image directory name. Default: `assets`
- `--mode`: `split` or `inline`. Default: `split`
- `--index-format`: `md`, `json`, or `both`. Default: `both`
- `--table-mode`: `auto`, `markdown`, or `html`. Default: `auto`
- `--overwrite`: replace an existing non-empty output directory
- `--verbose`: print detailed progress logs

Split mode produces:

- `index.md`
- `summary.json`
- `assets/`
- nested chunk directories such as `overview/index.md`

Inline mode produces:

- `index.md`
- `assets/`

## Public Example

The repository includes one synthetic sample document for demos and smoke tests:

- [example/sample.docx](example/sample.docx)
- [example/README.md](example/README.md)

The sample is intentionally fictitious and contains no internal business content.

## Development

Run the test suite:

```bash
uv run pytest -q
```

Build local binaries with PyInstaller:

```bash
uv run python scripts/build_binary.py --clean
```

Supported local build targets:

- `macos-arm64`
- `windows-x64`

Cross-platform builds are intentionally rejected. Build each binary on its native host.

## Release Process

Public binaries are distributed through GitHub Releases:

- `documind-macos-arm64`
- `documind-windows-x64.exe`

Recommended release flow:

1. Build on each supported host.
2. Run a smoke test against `example/sample.docx`.
3. Upload the binaries as GitHub release assets.

Smoke test examples:

```bash
./release/documind-macos-arm64 --help
./release/documind-macos-arm64 convert example/sample.docx --out-dir ./tmp/smoke --overwrite
```

```powershell
.\release\documind-windows-x64.exe --help
.\release\documind-windows-x64.exe convert example\sample.docx --out-dir .\tmp\smoke --overwrite
```

The install script reads binaries from:

- `https://github.com/crow/documind/releases/latest/download`

You can override that base URL when testing mirrors or forks:

```bash
DOCUMIND_RELEASE_BASE_URL=https://downloads.example.org/documind sh install.sh
```

## Unsigned macOS Binary Note

The macOS binary is unsigned. If Gatekeeper blocks it after download:

```bash
xattr -dr com.apple.quarantine ~/.local/bin/documind
chmod +x ~/.local/bin/documind
```

## Limitations

- Input format is currently limited to `.docx`.
- The CLI processes one document at a time.
- Local binary packaging currently supports only `macos-arm64` and `windows-x64`.
- Linux binaries are not packaged in this repository yet.
- External links are preserved, but linked files are not downloaded into the output directory.

## License

[MIT](LICENSE)
