#!/bin/bash

# Bitcrusher Installation Script

set -e

echo "Installing Bitcrusher GUI for GNOME..."
echo ""

SUDO_CMD=""
if [[ $EUID -ne 0 ]]; then
    if command -v sudo &> /dev/null; then
        SUDO_CMD="sudo"
    else
        echo "Error: sudo is required to install system packages. Please rerun this script as root or install sudo."
        exit 1
    fi
fi

run_with_privileges() {
    if [[ -n "$SUDO_CMD" ]]; then
        "$SUDO_CMD" "$@"
    else
        "$@"
    fi
}

PIP_INSTALL_FLAGS=(--user)

install_pygobject_packages() {
    if command -v apt &> /dev/null; then
        echo "Detected apt-based system (Ubuntu/Debian/Pop/Mint)"
        if ! run_with_privileges apt update; then
            return 1
        fi
        if ! run_with_privileges apt install -y python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1; then
            return 1
        fi
        # Development headers required for pip builds (best-effort)
        run_with_privileges apt install -y libgirepository1.0-dev libcairo2-dev libgtk-4-dev libadwaita-1-dev build-essential pkg-config python3-dev >/dev/null 2>&1 || true
        return 0
    elif command -v dnf &> /dev/null; then
        echo "Detected dnf-based system (Fedora/RHEL/CentOS)"
        if ! run_with_privileges dnf install -y python3-gobject gtk4 libadwaita libadwaita-devel gobject-introspection-devel cairo-devel gcc pkgconf-pkg-config python3-devel; then
            return 1
        fi
        return 0
    elif command -v pacman &> /dev/null; then
        echo "Detected pacman-based system (Arch/Manjaro)"
        if ! run_with_privileges pacman -S --needed --noconfirm python-gobject gtk4 libadwaita gobject-introspection cairo base-devel; then
            return 1
        fi
        return 0
    fi

    return 1
}

install_pygobject_with_pip() {
    echo "Attempting PyGObject installation via pip (fallback)"
    if ! python3 -m pip install "${PIP_INSTALL_FLAGS[@]}" --upgrade pip setuptools wheel pycairo; then
        return 1
    fi
    if ! python3 -m pip install "${PIP_INSTALL_FLAGS[@]}" --upgrade PyGObject; then
        return 1
    fi
    return 0
}

ensure_pygobject() {
    echo ""
    echo "Checking Python dependencies..."

    if python3 -c "import gi" 2>/dev/null; then
        echo "✓ PyGObject already installed"
        return 0
    fi

    echo "PyGObject not found. Installing system packages..."
    if install_pygobject_packages; then
        if python3 -c "import gi" 2>/dev/null; then
            echo "✓ PyGObject installed via system packages"
            return 0
        fi
    else
        echo "System package installation unavailable or failed (continuing with pip)."
    fi

    echo "Installing PyGObject for the current Python interpreter via pip..."
    if install_pygobject_with_pip && python3 -c "import gi" 2>/dev/null; then
        echo "✓ PyGObject installed via pip"
        return 0
    fi

    echo ""
    echo "Error: PyGObject installation failed even after automated attempts."
    echo "Ensure GTK4/libadwaita development files are available and rerun this script."
    exit 1
}

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "Error: This script is designed for Linux systems"
    exit 1
fi

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Check for pip
if ! command -v pip3 &> /dev/null && ! python3 -m pip --version &> /dev/null; then
    echo "Error: pip is not installed"
    echo "Install it with: sudo apt install python3-pip"
    exit 1
fi

# Detect if we're running inside a virtual environment to decide pip scope
if python3 - <<'PY' >/dev/null 2>&1; then
import sys
if getattr(sys, "base_prefix", sys.prefix) != sys.prefix:
    raise SystemExit(0)
if hasattr(sys, "real_prefix"):
    raise SystemExit(0)
raise SystemExit(1)
PY
    PIP_INSTALL_FLAGS=()
fi

# Check for Node.js
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is not installed"
    exit 1
fi

# Install Node.js dependencies
echo "Installing Node.js dependencies..."
npm install

# Ensure PyGObject is present for the GUI
ensure_pygobject

# Install Python package
echo ""
echo "Installing Python package..."
python3 -m pip install "${PIP_INSTALL_FLAGS[@]}" -e . --no-deps

# Install desktop entry
echo "Installing desktop entry..."
mkdir -p ~/.local/share/applications
cp bitcrusher.desktop ~/.local/share/applications/

# Update desktop database
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database ~/.local/share/applications 2>/dev/null || true
fi

echo ""
echo "✓ Installation complete!"
echo ""
echo "You can now:"
echo "  1. Run from command line: bitcrusher"
echo "  2. Launch from GNOME Applications menu (search for 'Bitcrusher')"
echo ""
echo "Note: Make sure ~/.local/bin is in your PATH to use the 'bitcrusher' command."
echo "Add this to your ~/.bashrc if needed: export PATH=\"\$HOME/.local/bin:\$PATH\""
echo ""
