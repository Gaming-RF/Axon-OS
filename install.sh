#!/usr/bin/env bash
# Axon OS — Installer
# AI-Native Linux Desktop
set -euo pipefail

# ---------------------------------------------------------------------------
# ANSI color helpers (degrade gracefully when tput is unavailable)
# ---------------------------------------------------------------------------
if command -v tput &>/dev/null && tput setaf 1 &>/dev/null 2>&1; then
    RED="$(tput setaf 1)"
    GREEN="$(tput setaf 2)"
    YELLOW="$(tput setaf 3)"
    CYAN="$(tput setaf 6)"
    BOLD="$(tput bold)"
    RESET="$(tput sgr0)"
else
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[0;33m'
    CYAN='\033[0;36m'
    BOLD='\033[1m'
    RESET='\033[0m'
fi

info()    { printf "${CYAN}  ℹ  %s${RESET}\n" "$*"; }
success() { printf "${GREEN}  ✔  %s${RESET}\n" "$*"; }
warn()    { printf "${YELLOW}  ⚠  %s${RESET}\n" "$*"; }
error()   { printf "${RED}  ✖  %s${RESET}\n" "$*" >&2; }
step()    { printf "\n${BOLD}${CYAN}══▶  %s${RESET}\n" "$*"; }

# ---------------------------------------------------------------------------
# ASCII banner
# ---------------------------------------------------------------------------
printf "${CYAN}"
cat <<'BANNER'
╔═══════════════════════════════════════╗
║          ⬡  AXON  OS  v0.1           ║
║   AI-Native Linux Desktop             ║
╚═══════════════════════════════════════╝
BANNER
printf "${RESET}\n"

# ---------------------------------------------------------------------------
# PREFLIGHT CHECKS
# ---------------------------------------------------------------------------
step "Running preflight checks"

# Must not be root
if [[ "${EUID}" -eq 0 ]]; then
    error "Do not run this installer as root. Run as your regular user."
    exit 1
fi
success "Running as non-root user: ${USER}"

# Python 3.11+
if ! python3 -c "import sys; assert sys.version_info >= (3,11)" 2>/dev/null; then
    error "Python 3.11 or newer is required. Install it and retry."
    exit 1
fi
PYVER="$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')"
success "Python ${PYVER} found"

# Ubuntu
if ! grep -q 'ID=ubuntu' /etc/os-release 2>/dev/null; then
    error "Axon OS requires Ubuntu. This system does not appear to be Ubuntu."
    exit 1
fi
success "Ubuntu detected"

# GNOME available
if [[ -z "${GNOME_SHELL_SESSION_MODE:-}" ]] && ! command -v gnome-shell &>/dev/null; then
    error "GNOME Shell is not available. Axon OS requires a GNOME session."
    exit 1
fi
success "GNOME Shell available"

# Resolve installer directory (follow symlinks)
SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"

# ---------------------------------------------------------------------------
# STEP 1: Install Python / GTK dependencies
# ---------------------------------------------------------------------------
step "Step 1/8 — Installing Python/GTK dependencies"
sudo apt-get install -y \
    python3-gi \
    python3-gi-cairo \
    gir1.2-gtk-4.0 \
    gir1.2-adw-1 \
    python3-httpx
success "Python/GTK dependencies installed"

# ---------------------------------------------------------------------------
# STEP 2: Install Ollama
# ---------------------------------------------------------------------------
step "Step 2/8 — Installing Ollama"
if command -v ollama &>/dev/null; then
    info "Ollama already installed at $(command -v ollama) — skipping"
else
    info "Downloading and installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
    success "Ollama installed"
fi

# ---------------------------------------------------------------------------
# STEP 3: Interactive model selection
# ---------------------------------------------------------------------------
step "Step 3/8 — Select an AI model to download"
printf "\n"
printf "  ${BOLD}1)${RESET} llama3.2:3b   ${GREEN}(Recommended)${RESET} — fast, lightweight\n"
printf "  ${BOLD}2)${RESET} mistral:7b    — strong reasoning\n"
printf "  ${BOLD}3)${RESET} qwen2.5:7b    — multilingual, balanced\n"
printf "  ${BOLD}s)${RESET} Skip          — do not pull a model now\n"
printf "\n"
read -rp "  Choose [1/2/3/s]: " MODEL_CHOICE

case "${MODEL_CHOICE}" in
    1) OLLAMA_MODEL="llama3.2:3b" ;;
    2) OLLAMA_MODEL="mistral:7b" ;;
    3) OLLAMA_MODEL="qwen2.5:7b" ;;
    s|S)
        info "Skipping model download"
        OLLAMA_MODEL=""
        ;;
    *)
        warn "Unrecognised choice '${MODEL_CHOICE}', defaulting to llama3.2:3b"
        OLLAMA_MODEL="llama3.2:3b"
        ;;
esac

if [[ -n "${OLLAMA_MODEL}" ]]; then
    info "Pulling model: ${OLLAMA_MODEL}"
    ollama pull "${OLLAMA_MODEL}"
    success "Model ${OLLAMA_MODEL} ready"
fi

# ---------------------------------------------------------------------------
# STEP 4: Install GNOME extension
# ---------------------------------------------------------------------------
step "Step 4/8 — Installing GNOME Shell extension"
DEST="${HOME}/.local/share/gnome-shell/extensions/axon-shell@axon-os"
mkdir -p "${DEST}"
cp -r "${SCRIPT_DIR}/shell/axon-shell/." "${DEST}/"

if command -v glib-compile-schemas &>/dev/null; then
    glib-compile-schemas "${DEST}/schemas/" 2>/dev/null || true
fi

gnome-extensions enable axon-shell@axon-os 2>/dev/null \
    || warn "Restart GNOME Shell to enable the extension (Alt+F2 → r, or log out and back in)"
success "GNOME extension installed to ${DEST}"

# ---------------------------------------------------------------------------
# STEP 5: Install GTK theme
# ---------------------------------------------------------------------------
step "Step 5/8 — Installing Axon GTK theme"
mkdir -p "${HOME}/.themes/axon-gtk/gtk-4.0"
cp "${SCRIPT_DIR}/theme/axon-gtk/gtk-dark.css" \
   "${HOME}/.themes/axon-gtk/gtk-4.0/gtk.css"
cp "${SCRIPT_DIR}/theme/axon-gtk/index.theme" \
   "${HOME}/.themes/axon-gtk/"

gsettings set org.gnome.desktop.interface gtk-theme axon-gtk
gsettings set org.gnome.desktop.interface color-scheme prefer-dark
success "Axon GTK theme installed and applied"

# ---------------------------------------------------------------------------
# STEP 6: Install apps and .desktop files
# ---------------------------------------------------------------------------
step "Step 6/8 — Installing Axon OS applications"
APPS_DIR="${HOME}/.local/share/axon-os"
mkdir -p "${APPS_DIR}"
cp -r "${SCRIPT_DIR}/apps/"* "${APPS_DIR}/"

mkdir -p "${HOME}/.local/share/applications"
for f in "${SCRIPT_DIR}/data/applications/"*.desktop; do
    DEST_FILE="${HOME}/.local/share/applications/$(basename "${f}")"
    sed "s|AXON_APPS_DIR|${APPS_DIR}|g" "${f}" > "${DEST_FILE}"
    info "Installed $(basename "${f}")"
done
success "Applications installed to ${APPS_DIR}"

# ---------------------------------------------------------------------------
# STEP 7: Configure GNOME workspaces
# ---------------------------------------------------------------------------
step "Step 7/8 — Configuring GNOME workspaces"
gsettings set org.gnome.desktop.wm.preferences num-workspaces 9
gsettings set org.gnome.mutter dynamic-workspaces false
gsettings set org.gnome.desktop.interface enable-animations true
success "GNOME workspace configuration applied"

# ---------------------------------------------------------------------------
# STEP 8: Set up autostart for firstboot.sh
# ---------------------------------------------------------------------------
step "Step 8/8 — Configuring first-boot autostart"
mkdir -p "${HOME}/.config/autostart"

FIRSTBOOT_SCRIPT="${SCRIPT_DIR}/build/config/firstboot.sh"
chmod +x "${FIRSTBOOT_SCRIPT}"

cat > "${HOME}/.config/autostart/axon-firstboot.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Axon OS First Boot Setup
Comment=Runs once on first login to complete Axon OS setup
Exec=bash ${FIRSTBOOT_SCRIPT}
Icon=axon-os
Terminal=false
StartupNotify=false
X-GNOME-Autostart-enabled=true
X-GNOME-Autostart-Phase=Applications
EOF

success "First-boot autostart configured"

# ---------------------------------------------------------------------------
# Completion banner
# ---------------------------------------------------------------------------
printf "\n"
printf "${GREEN}${BOLD}"
cat <<'SUCCESS'
╔══════════════════════════════════════════════════════╗
║        Axon OS installed successfully!               ║
║                                                      ║
║  Log out and back in to activate all components.     ║
║                                                      ║
║  Super+Space  =  Intent Bar                          ║
║  Super+A      =  AI Panel                            ║
╚══════════════════════════════════════════════════════╝
SUCCESS
printf "${RESET}\n"
