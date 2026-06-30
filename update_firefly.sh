#!/usr/bin/env bash

set -e
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load deployment configuration. This script is meant to be installed onto your
# PATH (e.g. ~/.local/bin), so we do NOT look beside the script first — we look
# in a real config location. Lookup order, first match wins:
#   1. $MONEYWIZ_CONFIG            explicit override (error if set but missing)
#   2. $XDG_CONFIG_HOME (or ~/.config)/moneywiz-to-firefly/config
#   3. <dir of this script>/config  convenience when run from a checkout
# See update_firefly.config.dist for the file format.
CONFIG_HOME="${XDG_CONFIG_HOME:-${HOME}/.config}"
if [ -n "${MONEYWIZ_CONFIG:-}" ]; then
    if [ ! -f "${MONEYWIZ_CONFIG}" ]; then
        echo "Error: MONEYWIZ_CONFIG is set but '${MONEYWIZ_CONFIG}' does not exist" 1>&2
        exit 1
    fi
    DEPLOY_CONFIG="${MONEYWIZ_CONFIG}"
elif [ -f "${CONFIG_HOME}/moneywiz-to-firefly/config" ]; then
    DEPLOY_CONFIG="${CONFIG_HOME}/moneywiz-to-firefly/config"
elif [ -f "${SCRIPT_DIR}/config" ]; then
    DEPLOY_CONFIG="${SCRIPT_DIR}/config"
else
    DEPLOY_CONFIG=""
fi

if [ -n "${DEPLOY_CONFIG}" ]; then
    set -a
    # shellcheck disable=SC1090
    . "${DEPLOY_CONFIG}"
    set +a
fi

# Show usage
usage() {
    cat << USAGE
Deploy a MoneyWiz CSV report to a remote Firefly III host and run import/export there.

Usage:
    $(basename "$0") [options] csv_report_file

Options:
    -i, --import   Do only the report import
    -e, --export   Do only the database export
    -h, --help     This help output
    -V, --version  Show version

Configuration (via the environment or a config file, see update_firefly.config.dist).
Config file lookup order: \$MONEYWIZ_CONFIG, then
\${XDG_CONFIG_HOME:-~/.config}/moneywiz-to-firefly/config, then ./config beside this script.
    DEPLOY_SSH_HOST     SSH host to deploy to (e.g. "user@host" or a ~/.ssh/config alias)
    DEPLOY_REMOTE_PATH  Base dir on the host holding reports/, db/, and config.json
    DEPLOY_PROJECT_DIR  Path to the moneywiz-to-firefly checkout on the host
    DEPLOY_PATH_PREFIX  Optional: dir to prepend to PATH on the host so uv is found
                        (see update_firefly.config.dist; leave unset to keep the host's PATH as-is)

Examples:
    $(basename "$0") report.csv
USAGE
    if [ -n "$*" ]; then
        echo 1>&2
        echo "Error: $*" 1>&2
        exit 1
    else
        exit 0
    fi
}

IMPORT=0
EXPORT=0

# Parse parameters
while [ "${1+isset}" ]; do
    case "$1" in
        -h|--help)
            usage
        ;;
        -V|--version)
            echo "$(basename "$0")-2.0"
            exit 0
        ;;
        -i|--import)
            IMPORT=1
        ;;
        -e|--export)
            EXPORT=1
        ;;
        --)
            break
        ;;
        -*)
            usage "Unknown option '$*'"
        ;;
        *)
            break
        ;;
    esac
    shift
done

# It's either 0 or 1, but we should force to 1
if [[ ${IMPORT} = "${EXPORT}" ]]; then
  IMPORT=1
  EXPORT=1
fi

# If empty parameters - show usage
[ -z "$*" ] && [ ${IMPORT} = "1" ] && usage

# Required deployment configuration (from the config file or the environment).
CONFIG_HINT="copy update_firefly.config.dist to ${CONFIG_HOME}/moneywiz-to-firefly/config and fill it in"
: "${DEPLOY_SSH_HOST:?is not set — ${CONFIG_HINT}}"
: "${DEPLOY_REMOTE_PATH:?is not set — ${CONFIG_HINT}}"
: "${DEPLOY_PROJECT_DIR:?is not set — ${CONFIG_HINT}}"

# Normalize the remote path to end with a single slash.
DEPLOY_REMOTE_PATH="${DEPLOY_REMOTE_PATH%/}/"

# Optional dir prepended to PATH on the host so `uv` is found (set in the config). Empty
# (unset) leaves the host's login PATH untouched.
DEPLOY_PATH_PREFIX="${DEPLOY_PATH_PREFIX:-}"

IMPORT_CMD=""
EXPORT_CMD=""

if [[ ${IMPORT} = "1" ]]; then
  REPORT_FILE_PATH="$1"
  REPORT_FILE_NAME=$(basename "$REPORT_FILE_PATH")
  # Copy the report to the host as-is; the importer handles the MoneyWiz "sep=,"hint line.
  # The remote path is built from local config, so client-side expansion is intended.
  # shellcheck disable=SC2029
  ssh "${DEPLOY_SSH_HOST}" "cat > \"${DEPLOY_REMOTE_PATH}reports/${REPORT_FILE_NAME}\"" < "$REPORT_FILE_PATH"

  IMPORT_CMD="uv run --directory ${DEPLOY_PROJECT_DIR} moneywiz-to-firefly --dedup --dbpath ${DEPLOY_REMOTE_PATH}db ${DEPLOY_REMOTE_PATH}reports/${REPORT_FILE_NAME};"
fi
if [[ ${EXPORT} = "1" ]]; then
  EXPORT_CMD="uv run --directory ${DEPLOY_PROJECT_DIR} moneywiz-to-firefly --dbpath ${DEPLOY_REMOTE_PATH}db --config ${DEPLOY_REMOTE_PATH}config.json --export;"
fi

# Prepend DEPLOY_PATH_PREFIX to the host's PATH (so `uv` is found) only if set.
PATH_EXPORT=""
if [ -n "${DEPLOY_PATH_PREFIX}" ]; then
  PATH_EXPORT="export PATH=\"${DEPLOY_PATH_PREFIX}:\$PATH\";"
fi

# Run command remotely.
ssh "${DEPLOY_SSH_HOST}" -t "${PATH_EXPORT}${IMPORT_CMD}${EXPORT_CMD}"
