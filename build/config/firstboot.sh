#!/usr/bin/env bash
# Axon OS — First Boot Configuration Script
# Runs once on the user's first login. Subsequent logins are no-ops.
set -euo pipefail

DONE="${HOME}/.config/axon-os/.firstboot-done"

# Guard: skip if already completed
[[ -f "${DONE}" ]] && exit 0

mkdir -p "${HOME}/.config/axon-os"

# ---------------------------------------------------------------------------
# Configure workspace names
# ---------------------------------------------------------------------------
gsettings set org.gnome.desktop.wm.preferences workspace-names \
    "[Code,Web,Chat,Files,Media,Work,Personal,Terminal,Notes]"

# ---------------------------------------------------------------------------
# Start Ollama service (if installed and not already running)
# ---------------------------------------------------------------------------
if command -v ollama &>/dev/null; then
    if ! pgrep -x ollama &>/dev/null; then
        ollama serve &>/dev/null &
    fi
fi

# ---------------------------------------------------------------------------
# Launch welcome app (if present)
# ---------------------------------------------------------------------------
APPS_DIR="${HOME}/.local/share/axon-os"
if [[ -f "${APPS_DIR}/axon-welcome/main.py" ]]; then
    python3 "${APPS_DIR}/axon-welcome/main.py" &
fi

# ---------------------------------------------------------------------------
# Mark first-boot complete
# ---------------------------------------------------------------------------
touch "${DONE}"

exit 0
