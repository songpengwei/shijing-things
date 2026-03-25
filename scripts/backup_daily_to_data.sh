#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TARGET_ROOT="/home/muniao/data"
DATE_DIR="$(date +%F)"
BACKUP_DIR="${TARGET_ROOT}/${DATE_DIR}"

mkdir -p "${BACKUP_DIR}"

"${PROJECT_ROOT}/scripts/backup_runtime_data.sh" --backup-dir "${BACKUP_DIR}"

find "${TARGET_ROOT}" -mindepth 1 -maxdepth 1 -type d \
    -regextype posix-extended -regex '.*/[0-9]{4}-[0-9]{2}-[0-9]{2}$' \
    ! -newermt '3 days ago 00:00:00' \
    -exec rm -rf {} +
