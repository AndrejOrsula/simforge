#!/usr/bin/env bash

## Ensure that Blender is installed
command -v blender >/dev/null 2>&1 || {
    echo >&2 -e "\033[1;31m[$(date +%H:%M:%S)] ERROR    Blender is not in \$PATH\033[0m"
    exit 1
}

## Filter args from unused Python flags
args=()
for arg in "$@"; do
    if [[ "$arg" == "-I" || "$arg" == "-c" ]]; then
        continue
    fi
    args+=("$arg")
done

## Process args
if [[ "${#args[@]}" -eq "0" ]]; then
    echo >&2 -e "\033[1;31m[$(date +%H:%M:%S)] ERROR    At least one argument is required\033[0m"
    exit 2
elif [[ "${#args[@]}" -eq "1" ]]; then
    PYTHON_EXPR="import sys;sys.argv=[sys.argv[0]];${args[0]}"
else
    PYTHON_EXPR="import sys;sys.argv=[sys.argv[0],*sys.argv[sys.argv.index('--')+1:]];${args[0]}"
    OTHER_ARGS=(-- "${args[@]:1}")
fi

## Run Python expression in a Blender process
BLENDER_CMD=(
    blender
    --factory-startup
    --background
    --offline-mode
    --quiet
    --enable-autoexec
    --python-exit-code 1
    --python-expr "${PYTHON_EXPR}"
    "${OTHER_ARGS[@]}"
)
if [[ "${SF_LOG_LEVEL:-}" == "debug" ]]; then
    echo -e "\033[1;90m[$(date +%H:%M:%S)] DEBUG    ${BLENDER_CMD[*]//b\'[^\']*\'/<BIN>}\033[0m"
fi
exec "${BLENDER_CMD[@]}"
