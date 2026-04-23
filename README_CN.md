# documind

`documind` 是一个本地 CLI，用来把 `.docx` 文档转换成适合 LLM、RAG 与文档处理流水线消费的 Markdown 集合。它会提取标题、正文、图片和表格，并输出为按标题切分的 Markdown 目录树，或单文件 Markdown。

[English README](README.md)

## 功能

- 将 `.docx` 转换为适合下游 AI 工作流消费的 Markdown。
- 按标题层级切分输出，生成嵌套 chunk 目录。
- 导出内嵌图片到 `assets/`，并自动改写引用路径。
- 保留外部超链接和常见行内样式。
- 简单表格输出为 Markdown，复杂合并表格回退为 HTML。
- 支持 `split` 模式输出 chunk 集合，也支持 `inline` 模式输出单个 `index.md`。

## 安装

### macOS arm64 二进制安装

```bash
curl -fsSL https://raw.githubusercontent.com/crow/documind/main/install.sh | sh
```

安装脚本会从 GitHub Releases 下载最新的 macOS arm64 二进制，并放到 `~/.local/bin/documind`。

安装后验证：

```bash
documind --help
```

如果 `~/.local/bin` 还没有加入 `PATH`：

```bash
export PATH="$HOME/.local/bin:$PATH"
```

### 源码安装

环境要求：

- Python `>=3.11`
- `uv`

安装项目和开发依赖：

```bash
uv sync --extra dev
```

运行 CLI：

```bash
uv run documind --help
```

## 快速开始

把公开样例转换成分块 Markdown：

```bash
uv run documind convert example/sample.docx --out-dir ./output --split-level 2
```

生成单文件 Markdown：

```bash
uv run documind convert example/sample.docx --out-dir ./output-inline --mode inline
```

常用参数：

- `--out-dir`：输出目录，默认 `dist/<doc-stem>`
- `--split-level`：按标题切分的层级，默认 `2`
- `--assets-dir`：图片导出目录名，默认 `assets`
- `--mode`：`split` 或 `inline`，默认 `split`
- `--index-format`：`md`、`json` 或 `both`，默认 `both`
- `--table-mode`：`auto`、`markdown` 或 `html`，默认 `auto`
- `--overwrite`：覆盖已存在且非空的输出目录
- `--verbose`：输出详细日志

`split` 模式输出：

- `index.md`
- `summary.json`
- `assets/`
- 按标题生成的嵌套目录，例如 `overview/index.md`

`inline` 模式输出：

- `index.md`
- `assets/`

## 公开样例

仓库内包含一个公开的合成样例，用于演示和 smoke test：

- [example/sample.docx](example/sample.docx)
- [example/README.md](example/README.md)

该样例内容完全虚构，不包含企业内部业务文档。

## 开发

运行测试：

```bash
uv run pytest -q
```

使用 PyInstaller 构建本地二进制：

```bash
uv run python scripts/build_binary.py --clean
```

当前支持的本地构建目标：

- `macos-arm64`
- `windows-x64`

不支持跨平台构建，请在对应原生宿主机上分别打包。

## 发布流程

公开二进制通过 GitHub Releases 分发：

- `documind-macos-arm64`
- `documind-windows-x64.exe`

建议发布流程：

1. 在每个支持的平台上本地构建。
2. 使用 `example/sample.docx` 做 smoke test。
3. 将产物上传为 GitHub release assets。

Smoke test 示例：

```bash
./release/documind-macos-arm64 --help
./release/documind-macos-arm64 convert example/sample.docx --out-dir ./tmp/smoke --overwrite
```

```powershell
.\release\documind-windows-x64.exe --help
.\release\documind-windows-x64.exe convert example\sample.docx --out-dir .\tmp\smoke --overwrite
```

安装脚本默认从以下地址读取二进制：

- `https://github.com/crow/documind/releases/latest/download`

如需在镜像或 fork 上验证，可以覆盖：

```bash
DOCUMIND_RELEASE_BASE_URL=https://downloads.example.org/documind sh install.sh
```

## macOS 未签名说明

当前 macOS 二进制未签名。如果下载后被 Gatekeeper 拦截：

```bash
xattr -dr com.apple.quarantine ~/.local/bin/documind
chmod +x ~/.local/bin/documind
```

## 当前限制

- 当前只支持 `.docx` 输入。
- CLI 一次只处理一个文档。
- 本仓库当前只支持 `macos-arm64` 与 `windows-x64` 的本地打包。
- 暂不提供 Linux 二进制。
- 外部链接会被保留，但不会自动把目标文件下载到输出目录。

## 许可证

[MIT](LICENSE)
