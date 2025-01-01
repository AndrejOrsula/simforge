#!/usr/bin/env bash

## Ensure that Blender is installed
command -v blender >/dev/null 2>&1 || {
    echo >&2 -e "\033[1;31m[$(date +%H:%M:%S)] ERROR    Blender is not in \$PATH\033[0m"
    exit 1
}

## Process args
if [[ "${#}" -eq "0" ]]; then
    echo >&2 -e "\033[1;31m[$(date +%H:%M:%S)] ERROR    At least one argument is required\033[0m"
    exit 2
fi
if [[ ! -f "${1}" ]]; then
    echo >&2 -e "\033[1;31m[$(date +%H:%M:%S)] ERROR    Python file does not exist: ${1}\033[0m"
    exit 3
fi
PYTHON_FILE="$(realpath -e "${1}")"
OTHER_ARGS=(-- "${@:2}")

## Run Python expression in a Blender process
BLENDER_CMD=(
    blender
    --factory-startup
    --background
    --offline-mode
    --quiet
    --enable-autoexec
    --python-exit-code 1
    --python "${PYTHON_FILE}"
    "${OTHER_ARGS[@]}"
)
if [[ "${SF_LOG_LEVEL:-}" == "debug" ]]; then
    echo -e "\033[1;90m[$(date +%H:%M:%S)] DEBUG    ${BLENDER_CMD[*]}\033[0m"
fi
exec "${BLENDER_CMD[@]}"
