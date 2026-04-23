from pathlib import Path

from tests.conftest import ROOT


def test_release_workflow_builds_and_publishes_github_release():
    workflow = ROOT / ".github" / "workflows" / "release.yml"

    assert workflow.exists()
    content = workflow.read_text(encoding="utf-8")

    assert "push:" in content
    assert "tags:" in content
    assert "- 'v*'" in content or "- \"v*\"" in content
    assert "macos-latest" in content
    assert "windows-latest" in content
    assert "example/sample.docx" in content
    assert "documind-macos-arm64" in content
    assert "documind-windows-x64.exe" in content
    assert "softprops/action-gh-release" in content
