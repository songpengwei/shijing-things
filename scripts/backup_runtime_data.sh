#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TIMESTAMP="$(date -u +"%Y%m%dT%H%M%SZ")"
HOSTNAME_VALUE="$(hostname 2>/dev/null || echo unknown-host)"

BACKUP_BASE_DIR="${BACKUP_BASE_DIR:-${PROJECT_ROOT}/backups}"
ARCHIVE_PREFIX="${ARCHIVE_PREFIX:-shijing-runtime-backup}"
DB_PATH="${DB_PATH:-${PROJECT_ROOT}/shijing.db}"
ENV_PATH="${ENV_PATH:-${PROJECT_ROOT}/.env}"

INCLUDE_DATA_DIR=0
EXTRA_PATHS=()

usage() {
    cat <<'EOF'
Usage:
  ./scripts/backup_runtime_data.sh [options]

Options:
  --include-data           Include ./data in the backup archive
  --extra PATH             Include an extra file or directory; may be used multiple times
  --backup-dir DIR         Override output directory (default: ./backups)
  --db-path PATH           Override database path (default: ./shijing.db)
  --env-path PATH          Override env file path (default: ./.env)
  -h, --help               Show help

Environment variables:
  BACKUP_BASE_DIR          Same as --backup-dir
  DB_PATH                  Same as --db-path
  ENV_PATH                 Same as --env-path
  ARCHIVE_PREFIX           Backup archive filename prefix

Examples:
  ./scripts/backup_runtime_data.sh
  ./scripts/backup_runtime_data.sh --include-data
  ./scripts/backup_runtime_data.sh --extra /srv/shijing-things/uploads
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --include-data)
            INCLUDE_DATA_DIR=1
            shift
            ;;
        --extra)
            if [[ $# -lt 2 ]]; then
                echo "error: --extra requires a path" >&2
                exit 1
            fi
            EXTRA_PATHS+=("$2")
            shift 2
            ;;
        --backup-dir)
            if [[ $# -lt 2 ]]; then
                echo "error: --backup-dir requires a directory" >&2
                exit 1
            fi
            BACKUP_BASE_DIR="$2"
            shift 2
            ;;
        --db-path)
            if [[ $# -lt 2 ]]; then
                echo "error: --db-path requires a path" >&2
                exit 1
            fi
            DB_PATH="$2"
            shift 2
            ;;
        --env-path)
            if [[ $# -lt 2 ]]; then
                echo "error: --env-path requires a path" >&2
                exit 1
            fi
            ENV_PATH="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "error: unknown option: $1" >&2
            usage >&2
            exit 1
            ;;
    esac
done

mkdir -p "${BACKUP_BASE_DIR}"

STAGING_DIR="${BACKUP_BASE_DIR}/${ARCHIVE_PREFIX}-${TIMESTAMP}"
ARCHIVE_PATH="${BACKUP_BASE_DIR}/${ARCHIVE_PREFIX}-${TIMESTAMP}.tar.gz"

rm -rf "${STAGING_DIR}"
mkdir -p "${STAGING_DIR}"

copy_path_into_staging() {
    local source_path="$1"
    local label_path="$2"

    if [[ ! -e "${source_path}" ]]; then
        echo "warning: skip missing path: ${source_path}" >&2
        return 0
    fi

    local target_dir
    target_dir="$(dirname "${label_path}")"
    mkdir -p "${STAGING_DIR}/${target_dir}"
    cp -a "${source_path}" "${STAGING_DIR}/${label_path}"
}

if [[ -f "${ENV_PATH}" ]]; then
    copy_path_into_staging "${ENV_PATH}" ".env"
else
    echo "warning: env file not found: ${ENV_PATH}" >&2
fi

if [[ -f "${DB_PATH}" ]]; then
    mkdir -p "${STAGING_DIR}"
    if command -v sqlite3 >/dev/null 2>&1; then
        sqlite3 "${DB_PATH}" ".backup '${STAGING_DIR}/shijing.db'"
    else
        echo "warning: sqlite3 not found, falling back to file copy for database backup" >&2
        cp -a "${DB_PATH}" "${STAGING_DIR}/shijing.db"
    fi
else
    echo "warning: database file not found: ${DB_PATH}" >&2
fi

if [[ "${INCLUDE_DATA_DIR}" -eq 1 ]]; then
    copy_path_into_staging "${PROJECT_ROOT}/data" "data"
fi

for extra_path in "${EXTRA_PATHS[@]}"; do
    if [[ "${extra_path}" = /* ]]; then
        safe_name="$(echo "${extra_path}" | sed 's#^/##')"
    else
        safe_name="${extra_path#./}"
        extra_path="${PROJECT_ROOT}/${extra_path#./}"
    fi
    copy_path_into_staging "${extra_path}" "extra/${safe_name}"
done

cat > "${STAGING_DIR}/BACKUP_INFO.txt" <<EOF
created_at_utc=${TIMESTAMP}
hostname=${HOSTNAME_VALUE}
project_root=${PROJECT_ROOT}
env_path=${ENV_PATH}
db_path=${DB_PATH}
include_data_dir=${INCLUDE_DATA_DIR}
extra_paths=${EXTRA_PATHS[*]:-}
EOF

(
    cd "${BACKUP_BASE_DIR}"
    tar -czf "${ARCHIVE_PATH}" "$(basename "${STAGING_DIR}")"
)

rm -rf "${STAGING_DIR}"

echo "backup_created=${ARCHIVE_PATH}"
