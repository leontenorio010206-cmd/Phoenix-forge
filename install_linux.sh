#!/bin/sh
set -eu
cd "$(dirname "$0")"
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements/modern.txt -r requirements/test-modern.txt
printf 'Run: PF_PYTHON=.venv/bin/python ./run.sh\n'
