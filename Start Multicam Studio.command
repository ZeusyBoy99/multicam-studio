#!/bin/sh
# Double-click in Finder. Processing and media stay on this Mac.
set -eu
PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
export PATH
STUDIO_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$STUDIO_DIR"

fail() {
    printf '\n%s\n' "$1" >&2
    printf 'Press Return to close this window. '
    read -r answer || true
    exit 1
}

for binary in ffmpeg ffprobe; do
    command -v "$binary" >/dev/null 2>&1 || fail "Missing $binary. In Terminal, install it with: brew install ffmpeg"
done
command -v python3 >/dev/null 2>&1 || fail 'Python 3.10 or newer is required. Install it with: brew install python'

PYTHON="$STUDIO_DIR/.venv/bin/python"
if [ ! -x "$PYTHON" ]; then
    # Reuse a working recording environment when one already exists nearby.
    PYTHON=''
    for candidate in "$STUDIO_DIR"/../Recordings/*/.venv/bin/python; do
        if [ -x "$candidate" ] && "$candidate" -c 'import sys, numpy, scipy; assert sys.version_info >= (3, 10)' >/dev/null 2>&1; then
            PYTHON="$candidate"
            break
        fi
    done
    if [ -z "$PYTHON" ]; then
        python3 -c 'import sys; assert sys.version_info >= (3, 10)' >/dev/null 2>&1 || fail 'Python 3.10 or newer is required. Install it with: brew install python'
        printf 'Creating the local Python environment…\n'
        python3 -m venv "$STUDIO_DIR/.venv" || fail 'Could not create the Python environment. Check the folder is writable and Python is installed.'
        PYTHON="$STUDIO_DIR/.venv/bin/python"
    fi
fi
"$PYTHON" -c 'import sys; assert sys.version_info >= (3, 10)' >/dev/null 2>&1 || fail 'This Python environment is too old. Install Python 3.10 or newer and recreate the .venv folder.'
if ! "$PYTHON" -c 'import numpy, scipy' >/dev/null 2>&1; then
    printf 'Installing NumPy and SciPy (internet needed for this first setup)…\n'
    "$PYTHON" -m pip install -r "$STUDIO_DIR/requirements.txt" || fail 'Could not install dependencies. Check your internet connection, then reopen this launcher.'
fi
printf '\nMulticam Studio is starting in your browser.\nKeep this Terminal window open while editing or rendering.\nPress Control-C here to stop the local server.\n\n'
exec "$PYTHON" "$STUDIO_DIR/server.py" --open --default-folder "$STUDIO_DIR/.." "$@"
