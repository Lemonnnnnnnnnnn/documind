import os
from pathlib import Path
import shlex
import subprocess
import textwrap

import pytest

from tests.conftest import ROOT


pytestmark = pytest.mark.skipif(os.name == "nt", reason="install.sh is validated on macOS release jobs")


def _write_executable(path: Path, content: str) -> None:
    path.write_text(textwrap.dedent(content))
    path.chmod(path.stat().st_mode | 0o755)


def _shell_path(path: Path) -> str:
    if os.name != "nt":
        return str(path)

    result = subprocess.run(
        ["sh", "-lc", f"cygpath -u {shlex.quote(str(path))}"],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode == 0:
        return result.stdout.strip()

    normalized = str(path).replace("\\", "/")
    if len(normalized) >= 2 and normalized[1] == ":":
        return f"/{normalized[0].lower()}{normalized[2:]}"
    return normalized


def _build_install_env(
    tmp_path: Path,
    *,
    system: str = "Darwin",
    machine: str = "arm64",
    arm64_capable: str = "1",
    curl_exit_code: int = 0,
):
    home_dir = tmp_path / "home"
    fake_bin_dir = tmp_path / "fake-bin"
    curl_log = tmp_path / "curl.log"
    curl_log_shell = _shell_path(curl_log)

    home_dir.mkdir()
    fake_bin_dir.mkdir()

    _write_executable(
        fake_bin_dir / "uname",
        f"""#!/bin/sh
        case "$1" in
          -s) printf '%s\\n' "{system}" ;;
          -m) printf '%s\\n' "{machine}" ;;
          *) exit 1 ;;
        esac
        """,
    )
    _write_executable(
        fake_bin_dir / "sysctl",
        f"""#!/bin/sh
        if [ "$#" -eq 2 ] && [ "$1" = "-in" ] && [ "$2" = "hw.optional.arm64" ]; then
          printf '%s\\n' "{arm64_capable}"
          exit 0
        fi

        exit 1
        """,
    )
    _write_executable(
        fake_bin_dir / "curl",
        f"""#!/bin/sh
        set -eu

        output_path=''
        download_url=''

        while [ "$#" -gt 0 ]; do
          case "$1" in
            -o)
              output_path="$2"
              shift 2
              ;;
            -*)
              shift
              ;;
            *)
              download_url="$1"
              shift
              ;;
          esac
        done

        printf '%s\\n' "$download_url" > "{curl_log_shell}"
        if [ "{curl_exit_code}" -ne 0 ]; then
          exit "{curl_exit_code}"
        fi
        printf '%s\\n' '#!/bin/sh' 'echo installed-documind' > "$output_path"
        """,
    )

    env = os.environ.copy()
    env["HOME"] = _shell_path(home_dir)
    env["PATH"] = f"{fake_bin_dir}{os.pathsep}{env['PATH']}"
    return env, home_dir, curl_log


def test_install_script_installs_documind_to_user_local_bin(tmp_path):
    env, home_dir, curl_log = _build_install_env(tmp_path)

    result = subprocess.run(
        ["sh", str(ROOT / "install.sh")],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    installed_binary = home_dir / ".local" / "bin" / "documind"
    assert installed_binary.exists()
    assert os.access(installed_binary, os.X_OK)
    assert installed_binary.read_text() == "#!/bin/sh\necho installed-documind\n"
    assert f"Installed documind to {_shell_path(installed_binary)}" in result.stdout
    assert "Run 'documind --help' to verify the installation." in result.stdout
    assert f"Add {_shell_path(home_dir / '.local' / 'bin')} to PATH" in result.stdout
    assert (
        curl_log.read_text().strip()
        == "https://github.com/Lemonnnnnnnnnnn/documind/releases/latest/download/documind-macos-arm64"
    )


def test_install_script_allows_overriding_release_base_url(tmp_path):
    env, _, curl_log = _build_install_env(tmp_path)
    env["DOCUMIND_RELEASE_BASE_URL"] = "https://downloads.example.org/documind"

    result = subprocess.run(
        ["sh", str(ROOT / "install.sh")],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert curl_log.read_text().strip() == "https://downloads.example.org/documind/documind-macos-arm64"


def test_install_script_overwrites_existing_binary_without_leaving_temp_files(tmp_path):
    env, home_dir, _ = _build_install_env(tmp_path)
    install_dir = home_dir / ".local" / "bin"
    install_dir.mkdir(parents=True)
    installed_binary = install_dir / "documind"
    installed_binary.write_text("old-version\n")
    installed_binary.chmod(0o755)

    result = subprocess.run(
        ["sh", str(ROOT / "install.sh")],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert installed_binary.read_text() == "#!/bin/sh\necho installed-documind\n"
    assert list(install_dir.glob("documind.tmp.*")) == []


def test_install_script_rejects_unsupported_platform_before_download(tmp_path):
    env, home_dir, curl_log = _build_install_env(tmp_path, system="Linux", machine="x86_64")

    result = subprocess.run(
        ["sh", str(ROOT / "install.sh")],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "install.sh only supports macOS arm64." in result.stderr
    assert not (home_dir / ".local" / "bin" / "documind").exists()
    assert not curl_log.exists()


def test_install_script_supports_apple_silicon_from_rosetta_shell(tmp_path):
    env, home_dir, _ = _build_install_env(
        tmp_path,
        system="Darwin",
        machine="x86_64",
        arm64_capable="1",
    )

    result = subprocess.run(
        ["sh", str(ROOT / "install.sh")],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert (home_dir / ".local" / "bin" / "documind").exists()


def test_install_script_skips_path_hint_when_user_bin_is_already_on_path(tmp_path):
    env, home_dir, _ = _build_install_env(tmp_path)
    install_dir = home_dir / ".local" / "bin"
    env["PATH"] = f"{env['PATH']}{os.pathsep}{install_dir}"

    result = subprocess.run(
        ["sh", str(ROOT / "install.sh")],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert f"Add {_shell_path(install_dir)} to PATH" not in result.stdout


def test_install_script_preserves_existing_binary_when_download_fails(tmp_path):
    env, home_dir, _ = _build_install_env(tmp_path, curl_exit_code=22)
    install_dir = home_dir / ".local" / "bin"
    install_dir.mkdir(parents=True)
    installed_binary = install_dir / "documind"
    installed_binary.write_text("old-version\n")
    installed_binary.chmod(0o755)

    result = subprocess.run(
        ["sh", str(ROOT / "install.sh")],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 22
    assert installed_binary.read_text() == "old-version\n"
    assert list(install_dir.glob("documind.tmp.*")) == []
