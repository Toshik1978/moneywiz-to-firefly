#!/usr/bin/env bash

set -e
set -u

# Show usage
usage() {
    cat << USAGE
Update Firefly III with the new exported report
Usage:
    $(basename $0) csv_report_file

Options:
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

# Parse parameters
while [ "${1+isset}" ]; do
    case "$1" in
        -h|--help)
            usage
        ;;
        -V|--version)
            echo "$(basename $0)-1.0"
            exit 0
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

# If empty parameters - show usage
[ -z "$*" ] && usage

REPORT_FILE_PATH="$1"
REPORT_FILE_NAME=$(basename ${REPORT_FILE_PATH})
SERVER="datron-server"
SERVER_PATH="/srv/backup/finances/"

# Copy new report to the server
scp "$REPORT_FILE_PATH" "${SERVER}:${SERVER_PATH}reports/"

# Run import and export remotely
ssh $SERVER -t "set -e; pushd Development/moneywiz-to-firefly; \
source .venv/bin/activate; \
./moneywiz-to-firefly --dbpath ${SERVER_PATH}db ${SERVER_PATH}reports/${REPORT_FILE_NAME}; \
./moneywiz-to-firefly --dbpath ${SERVER_PATH}db --config ${SERVER_PATH}config.json --export; \
deactivate; \
popd"
