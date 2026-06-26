#!/usr/bin/env bash
# Build a Gumroad-ready tarball of the Radar Pro kit (configs, prompts, runbooks).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT_DIR="${ROOT}/dist"
ARCHIVE="${OUT_DIR}/radar-pro-kit.tar.gz"
KIT_DIR="${ROOT}/packaging/pro-kit"

mkdir -p "${OUT_DIR}"
tar -czf "${ARCHIVE}" \
  -C "${KIT_DIR}" \
  README.md \
  MANIFEST.md \
  configs \
  prompts \
  runbooks \
  scheduling

echo "Wrote ${ARCHIVE}"
