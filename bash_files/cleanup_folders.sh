#!/usr/bin/env bash
set -euo pipefail

# === Base directories ===
BASE_DIR="/home/id956955/apps/bics_sirius_sfrdb_api_etl"
DATA_DIR="$BASE_DIR/var/data"

# Keep latest N dated folders (YYYY-MM-DD)
MAX_DAYS=4

clean_date_folders() {
    local target_dir="$1"

    if [[ ! -d "$target_dir" ]]; then
        return
    fi

    # Collect YYYY-MM-DD folders
    mapfile -t folders < <(
        find "$target_dir" -maxdepth 1 -type d -printf "%f\n" \
        | grep -E "^[0-9]{4}-[0-9]{2}-[0-9]{2}$" \
        | sort
    )

    local count=${#folders[@]}

    if (( count <= MAX_DAYS )); then
        return
    fi

    local remove_count=$(( count - MAX_DAYS ))

    for ((i=0; i<remove_count; i++)); do
        old="${folders[$i]}"
        old_path="$target_dir/$old"
        rm -rf "$old_path"
    done
}

clean_date_folders "$DATA_DIR"


