#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python -m manim -qm --fps 30 scenes/station.py EstacaoV2
