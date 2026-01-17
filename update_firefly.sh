#!/usr/bin/env bash

set -e
set -u

# Show usage
usage() {
    cat << USAGE
Update Firefly III with the newly exported report
Usage:
    $(basename $0) [options] csv_report_file

Options:
    -i, --import   Do only the report import
    -e, --export   Do only the database export
    -h, --help     This help output
    -V, --version  Show version

Examples:
    $(basename $0) report.csv
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
            echo "$(basename $0)-1.1"
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

# Properly configure import/export commands
SERVER="datron-server"
SERVER_PATH="/srv/backup/finances/"

IMPORT_CMD=""
EXPORT_CMD=""

if [[ ${IMPORT} = "1" ]]; then
  REPORT_FILE_PATH="$1"
  sed -i '' '1d' $REPORT_FILE_PATH
  scp "$REPORT_FILE_PATH" "${SERVER}:${SERVER_PATH}reports/"

  REPORT_FILE_NAME=$(basename ${REPORT_FILE_PATH})
  IMPORT_CMD="uv run --directory ~/Development/moneywiz-to-firefly ~/Development/moneywiz-to-firefly/moneywiz-to-firefly --dedup --dbpath ${SERVER_PATH}db ${SERVER_PATH}reports/${REPORT_FILE_NAME};"
fi
if [[ ${EXPORT} = "1" ]]; then
  EXPORT_CMD="uv run --directory ~/Development/moneywiz-to-firefly ~/Development/moneywiz-to-firefly/moneywiz-to-firefly --dbpath ${SERVER_PATH}db --config ${SERVER_PATH}config.json --export;"
fi

# Run command remotely
ssh $SERVER -t "${IMPORT_CMD}${EXPORT_CMD}"
