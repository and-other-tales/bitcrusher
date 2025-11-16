#!/bin/bash

# Bitcrusher Installation Script

set -e

echo "Installing Bitcrusher GUI for GNOME..."
echo ""

install_pygobject_packages() {
    if command -v apt &> /dev/null; then
        echo "Detected apt-based system (Ubuntu/Debian/Pop/Mint)"
        if ! sudo apt update; then
            return 1
        fi
        if ! sudo apt install -y python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1; then
            return 1
        fi
        return 0
    elif command -v dnf &> /dev/null; then
        echo "Detected dnf-based system (Fedora/RHEL/CentOS)"
        if ! sudo dnf install -y python3-gobject gtk4 libadwaita; then
            return 1
        fi
        return 0
    elif command -v pacman &> /dev/null; then
        echo "Detected pacman-based system (Arch/Manjaro)"
        if ! sudo pacman -S --noconfirm python-gobject gtk4 libadwaita; then
            return 1
        fi
        return 0
    fi

    return 1
}

install_pygobject_with_pip() {
    echo "Attempting PyGObject installation via pip (fallback)"
    if ! python3 -m pip install --user --upgrade pip setuptools wheel pycairo; then
        return 1
    fi
    if ! python3 -m pip install --user --upgrade PyGObject; then
        return 1
    fi
    return 0
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

# Check for Node.js
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is not installed"
    exit 1
fi

# Install Node.js dependencies
echo "Installing Node.js dependencies..."
npm install

# Check for PyGObject (GTK)
echo ""
echo "Checking Python dependencies..."

if ! python3 -c "import gi" 2>/dev/null; then
    echo ""
    echo "PyGObject is not installed. Installing dependencies..."

    if ! install_pygobject_packages; then
        echo "Could not install PyGObject via the system package manager."
        echo "Trying pip-based installation (may require build dependencies)..."
        install_pygobject_with_pip || true
    fi

    if ! python3 -c "import gi" 2>/dev/null; then
        echo ""
        echo "Error: PyGObject installation failed"
        echo "Please install PyGObject manually for your distribution."
        echo ""
        echo "Ubuntu/Debian:"
        echo "  sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1"
        echo ""
        echo "Fedora:"
        echo "  sudo dnf install python3-gobject gtk4 libadwaita"
        echo ""
        echo "Arch Linux:"
        echo "  sudo pacman -S python-gobject gtk4 libadwaita"
        exit 1
    fi

    echo "✓ PyGObject installed successfully"
fi

# Install Python package
echo ""
echo "Installing Python package..."
python3 -m pip install --user -e . --no-deps

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
