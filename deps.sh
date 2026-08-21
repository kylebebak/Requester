#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

rm -rf deps
mkdir -p deps
touch deps/__init__.py

# For ST >= 4205, where 3.8 plugin host was replaced with 3.14; we keep jsonschema at `4.17.3`, because this was the last pure python release (later releases depend on compiled rust extensions)
uv pip install --target ./deps -r deps.txt --python 3.14
