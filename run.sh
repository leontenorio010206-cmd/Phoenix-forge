#!/bin/sh
set -eu
cd "$(dirname "$0")"
exec "${PF_PYTHON:-python3}" -m app "$@"
