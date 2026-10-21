#!/bin/sh
# PhœnixForge Linux x86_64 portable preview.
set -eu
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if ! command -v iverilog >/dev/null 2>&1 || ! command -v vvp >/dev/null 2>&1; then
  printf '%s\n' 'PhœnixForge: falta Icarus Verilog (iverilog y vvp) en PATH.' \
    'En Ubuntu/Debian: sudo apt install iverilog' \
    'Puedes abrir la interfaz, pero las simulaciones HDL necesitan Icarus.' >&2
fi
exec "$HERE/PhoenixForge" "$@"
