#!/bin/bash

# Bitcrusher Installation Script

set -e

echo "Installing Bitcrusher GUI for GNOME..."
echo ""

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
    echo "PyGObject is not installed."
    echo "Please install it using your package manager:"
    echo ""
    echo "Ubuntu/Debian:"
    echo "  sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1"
    echo ""
    echo "Fedora:"
    echo "  sudo dnf install python3-gobject gtk4 libadwaita"
    echo ""
    echo "Arch Linux:"
    echo "  sudo pacman -S python-gobject gtk4 libadwaita"
    echo ""
    exit 1
fi

# Install Python package
echo ""
echo "Installing Python package..."
pip3 install --user -e .

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
