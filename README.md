# Bitcrusher

A chiptune-style bitcrusher audio effect for WAV files with both CLI and GNOME GUI interfaces.

Transform your audio into authentic retro gaming sounds with presets for classic consoles like Game Boy, NES, Sega Genesis, SNES, and vintage computers like Commodore 64 and Atari 2600.

## Features

- **Multiple Interfaces**: Command-line tool and beautiful GNOME GUI
- **Classic Console Presets**: Authentic sound profiles for Game Boy, NES, Sega Genesis, SNES, C64, Atari 2600
- **Custom Parameters**: Fine-tune bit depth, sample rate reduction, and wet/dry mix
- **Advanced Effects**: Low-pass filtering, hard clipping, and mono downmixing for authentic retro sound
- **Modern & Retro Modes**: From subtle vintage warmth to extreme lo-fi destruction
- **Stereo Support**: Process both mono and stereo WAV files

## Installation

### GUI Installation (GNOME)

The GUI installer will automatically install all dependencies including PyGObject and GTK4:

```bash
git clone https://github.com/yourusername/bitcrusher.git
cd bitcrusher
chmod +x install-gui.sh
./install-gui.sh
```

After installation, you can:
- Run from terminal: `bitcrusher`
- Launch from GNOME Applications menu (search for "Bitcrusher")

### CLI-Only Installation

For command-line only (no GUI):

```bash
git clone https://github.com/yourusername/bitcrusher.git
cd bitcrusher
npm install
```

Make the CLI executable:
```bash
chmod +x index.js
```

Run directly with Node:
```bash
node index.js process input.wav output.wav --preset gameboy
```

Or install globally:
```bash
npm link
bitcrusher process input.wav output.wav --preset gameboy
```

## Requirements

### For CLI
- Node.js 14+
- npm

### For GUI
- Python 3.10+
- PyGObject (GTK 4.0)
- libadwaita
- GNOME desktop environment

The install script automatically detects and installs GUI dependencies on:
- Ubuntu/Debian/Linux Mint/Pop!_OS
- Fedora/RHEL/CentOS
- Arch Linux/Manjaro

## Usage

### GUI Usage

1. Launch Bitcrusher from Applications menu or run `bitcrusher` in terminal
2. Select an input WAV file
3. Choose a preset or customize parameters:
   - **Bit Depth**: Lower = more lo-fi (1-16 bits)
   - **Sample Rate Reduction**: Higher = more aliasing (1-32x)
   - **Wet/Dry Mix**: 0.0 = original, 1.0 = fully crushed
4. Optionally change output filename
5. Click "Process Audio"

### CLI Usage

#### Basic Usage

```bash
# Use a preset
bitcrusher process input.wav output.wav --preset gameboy

# Custom parameters
bitcrusher process input.wav output.wav -b 8 -s 4 -m 1.0

# Output filename is optional (creates input_crushed.wav)
bitcrusher process input.wav --preset nes
```

Or use Node.js directly:

```bash
node index.js process input.wav output.wav --preset gameboy
```

#### List Available Presets

```bash
bitcrusher presets
```

Or:

```bash
node index.js presets
```

#### Command Options

```
bitcrusher process <input> [output] [options]

Options:
  -p, --preset <name>        Use a preset (gameboy, nes, sega, snes, c64, atari, mild, heavy, extreme)
  -b, --bit-depth <number>   Bit depth (1-16)
  -s, --sample-rate <number> Sample rate reduction factor
  -m, --mix <number>         Wet/dry mix (0.0-1.0, default: 1.0)
  -h, --help                 Display help
```

## Presets

### Classic Consoles

| Preset | Description | Specs |
|--------|-------------|-------|
| `gameboy` | Classic Game Boy lo-fi sound with mono output | 4-bit, 8x reduction, 4kHz LP, mono |
| `nes` | Nintendo Entertainment System style | 4-bit, 6x reduction, 8kHz LP, mono |
| `sega` | Sega Genesis/Mega Drive FM synthesis style | 8-bit, 3x reduction, 12kHz LP, stereo |
| `snes` | Super Nintendo higher quality samples | 8-bit, 2x reduction, 15kHz LP, stereo |

### Retro Computers

| Preset | Description | Specs |
|--------|-------------|-------|
| `c64` | Commodore 64 SID chip sound | 8-bit, 4x reduction, 6kHz LP, mono |
| `atari` | Extremely lo-fi Atari 2600 sound | 3-bit, 10x reduction, 3kHz LP, mono |

### Modern Effects

| Preset | Description | Specs |
|--------|-------------|-------|
| `mild` | Subtle vintage digital sound | 12-bit, 2x reduction, 70% mix |
| `heavy` | Aggressive bitcrushed sound | 6-bit, 8x reduction, 5kHz LP, clipping |
| `extreme` | Maximum destruction | 2-bit, 16x reduction, 2kHz LP, clipping, mono |

## Examples

```bash
# Make your track sound like a Game Boy game
bitcrusher process song.wav song_gameboy.wav --preset gameboy

# Sega Genesis style with stereo
bitcrusher process music.wav music_genesis.wav --preset sega

# Custom lo-fi effect with 50% mix
bitcrusher process vocals.wav vocals_lofi.wav -b 6 -s 8 -m 0.5

# Extreme crushed effect
bitcrusher process drums.wav drums_crushed.wav --preset extreme
```

## Technical Details

The bitcrusher effect works by:

1. **Bit Depth Reduction**: Quantizes audio samples to fewer bits, creating characteristic digital distortion
2. **Sample Rate Reduction**: Sample-and-hold effect that reduces temporal resolution, creating aliasing artifacts
3. **Low-pass Filtering**: Simulates the limited frequency response of vintage DACs (digital-to-analog converters)
4. **Hard Clipping**: Emulates digital distortion of old console hardware
5. **Mono Downmixing**: Authentic mono output for systems that only had mono sound

### Audio Processing

- Supports 16-bit WAV files (input/output)
- Processes both mono and stereo files
- Maintains original sample rate in output
- Uses 32-bit float processing internally for quality

## Development

### Project Structure

```
bitcrusher/
├── bitcrusher.js          # Core audio processing engine
├── index.js               # CLI interface
├── bitcrusher.py          # GNOME GUI application
├── package.json           # Node.js dependencies
├── pyproject.toml         # Python package config
├── bitcrusher.desktop     # Desktop entry for GNOME
└── install-gui.sh         # Automated installer
```

### Running Tests

```bash
# Node.js tests
npm test

# Test the bitcrusher GUI
python3 test_bitcrusher_gui.py
```

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Feel free to:
- Report bugs
- Suggest new presets for other classic systems
- Add new audio processing features
- Improve documentation

## Acknowledgments

Inspired by the iconic sounds of:
- Nintendo Game Boy (1989)
- Nintendo Entertainment System (1983)
- Sega Genesis/Mega Drive (1988)
- Super Nintendo (1990)
- Commodore 64 (1982)
- Atari 2600 (1977)
