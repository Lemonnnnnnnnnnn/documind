from documind.cli import main

from tests.conftest import SAMPLE_DOCX


def test_cli_convert_command_writes_output(tmp_path):
    exit_code = main(
        [
            "convert",
            str(SAMPLE_DOCX),
            "--out-dir",
            str(tmp_path),
            "--split-level",
            "2",
        ]
    )

    assert exit_code == 0
    assert (tmp_path / "index.md").exists()
    assert (tmp_path / "summary.json").exists()
    assert (tmp_path / "overview" / "index.md").exists()
    assert (tmp_path / "overview" / "glossary" / "index.md").exists()


def test_cli_convert_command_writes_inline_output(tmp_path):
    exit_code = main(
        [
            "convert",
            str(SAMPLE_DOCX),
            "--out-dir",
            str(tmp_path),
            "--mode",
            "inline",
        ]
    )

    assert exit_code == 0
    assert (tmp_path / "index.md").exists()
    assert not (tmp_path / "summary.json").exists()
    assert not (tmp_path / "overview" / "index.md").exists()


def test_cli_returns_error_for_invalid_docx_payload(tmp_path):
    bad_docx = tmp_path / "broken.docx"
    bad_docx.write_text("not a zip file", encoding="utf-8")

    exit_code = main(["convert", str(bad_docx), "--out-dir", str(tmp_path / "out")])

    assert exit_code == 1
