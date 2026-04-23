#!/usr/bin/env sh

set -eu

RELEASE_BASE_URL="${DOCUMIND_RELEASE_BASE_URL:-https://github.com/Lemonnnnnnnnnnn/documind/releases/latest/download}"
DOWNLOAD_URL="${RELEASE_BASE_URL}/documind-macos-arm64"
INSTALL_DIR="${HOME}/.local/bin"
INSTALL_PATH="${INSTALL_DIR}/documind"

platform="$(uname -s)"
arch="$(uname -m)"
arm64_capable="0"

if [ "${platform}" = "Darwin" ]; then
  arm64_capable="$(sysctl -in hw.optional.arm64 2>/dev/null || printf '0')"
fi

if [ "${platform}" != "Darwin" ] || { [ "${arch}" != "arm64" ] && [ "${arm64_capable}" != "1" ]; }; then
  echo "install.sh only supports macOS arm64." >&2
  exit 1
fi

mkdir -p "${INSTALL_DIR}"

tmp_file="$(mktemp "${INSTALL_DIR}/documind.tmp.XXXXXX")"
trap 'rm -f "${tmp_file}"' EXIT INT TERM HUP

curl -fsSL "${DOWNLOAD_URL}" -o "${tmp_file}"
chmod +x "${tmp_file}"
mv -f "${tmp_file}" "${INSTALL_PATH}"

echo "Installed documind to ${INSTALL_PATH}"
echo "Run 'documind --help' to verify the installation."

path_has_install_dir=0
old_ifs="${IFS}"
IFS=":"
for path_entry in ${PATH}; do
  if [ "${path_entry%/}" = "${INSTALL_DIR}" ]; then
    path_has_install_dir=1
    break
  fi
done
IFS="${old_ifs}"

if [ "${path_has_install_dir}" -ne 1 ]; then
  echo "Add ${INSTALL_DIR} to PATH to run 'documind' directly."
fi
