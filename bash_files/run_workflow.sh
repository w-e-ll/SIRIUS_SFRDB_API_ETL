#!/usr/bin/env bash
set -euo pipefail

# ============================================================
#  Base paths
# ============================================================
BASE_DIR="/home/id956955/apps/bics_sirius_sfrdb_api_etl"
VENV_PYTHON="$BASE_DIR/venv/bin/python"
CONFIG_DIR="$BASE_DIR/etc"

# Load ~/.env safely
if [[ -f "$BASE_DIR/.env" ]]; then
    set -a
    # remove carriage returns
    source <(sed 's/\r$//' "$BASE_DIR/.env")
    set +a
fi

# ============================================================
#  Log file
# ============================================================
TS="$(date +'%Y%m%d_%H%M%S')"

FETCHER_MAIN="$BASE_DIR/bics_sirius_sfrdb_api/fetcher_main.py"
UPLOADER_MAIN="$BASE_DIR/bics_sirius_sfrdb_api/uploader_main.py"

"$VENV_PYTHON" "$FETCHER_MAIN" --config-dir "$CONFIG_DIR"
"$VENV_PYTHON" "$UPLOADER_MAIN" --config-dir "$CONFIG_DIR"
