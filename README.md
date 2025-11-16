# Bitcrusher

A GNOME application with GUI to apply bitcrusher effects to WAV files, creating authentic chiptune-style audio reminiscent of classic gaming consoles and retro computers.

## Features

- **Native GNOME GUI** - Beautiful GTK4/libadwaita interface
- Multiple classic console presets (Game Boy, NES, Sega Genesis, SNES, etc.)
- Retro computer emulation (C64, Atari 2600)
- Custom bit depth and sample rate reduction
- Low-pass filtering to simulate vintage DAC bandwidth limitations
- Hard clipping for authentic digital distortion
- Optional mono downmixing for true mono console sound
- Wet/dry mix control for subtle effects
- Support for mono and stereo WAV files

## Installation

Run the installation script:

```bash
./install-gui.sh
```

This will install all dependencies and set up the `bitcrusher` command.

## Usage

### GUI Application

After installation, launch the GUI:

```bash
bitcrusher
```

Or search for "Bitcrusher" in your GNOME Applications menu.

The GUI provides:
- Easy file selection
- Visual preset picker
- Interactive parameter controls
- Real-time status updates

### Command-Line Usage (Advanced)

You can also use the Node.js CLI directly for batch processing:

```bash
node index.js process input.wav -p gameboy
node index.js process input.wav -p nes
node index.js process input.wav -p sega
```

### CLI Examples

```bash
# Specify output file
node index.js process input.wav output.wav -p c64

# Custom parameters: 8-bit depth with 4x sample rate reduction
node index.js process input.wav -b 8 -s 4

# Combine preset with custom mix
node index.js process input.wav -p nes -m 0.7

# List all available presets
node index.js presets
```

## Available Presets

### Classic Consoles
- **gameboy** - Classic Game Boy lo-fi sound (4-bit, 8x reduction)
- **nes** - Nintendo Entertainment System style (4-bit, 6x reduction)
- **sega** - Sega Genesis/Mega Drive FM synthesis style (8-bit, 3x reduction)
- **snes** - Super Nintendo higher quality samples (8-bit, 2x reduction)

### Retro Computers
- **c64** - Commodore 64 SID chip sound (8-bit, 4x reduction)
- **atari** - Extremely lo-fi Atari 2600 sound (3-bit, 10x reduction)

### Modern Effects
- **mild** - Subtle vintage digital sound (12-bit, 2x reduction, 70% mix)
- **heavy** - Aggressive bitcrushed sound (6-bit, 8x reduction)
- **extreme** - Maximum destruction (2-bit, 16x reduction)

## Command-Line Reference

For advanced users and batch processing:

### `process` command

```
node index.js process <input> [output] [options]
```

**Arguments:**
- `<input>` - Input WAV file path (required)
- `[output]` - Output WAV file path (optional, defaults to `input_crushed.wav`)

**Options:**
- `-p, --preset <name>` - Use a preset (gameboy, nes, sega, snes, c64, atari, mild, heavy, extreme)
- `-b, --bit-depth <number>` - Bit depth (1-16)
- `-s, --sample-rate <number>` - Sample rate reduction factor (higher = more reduction)
- `-m, --mix <number>` - Wet/dry mix (0.0 = original, 1.0 = fully crushed)

### `presets` command

```
node index.js presets
```

Lists all available presets with descriptions and parameters.

## How It Works

The bitcrusher applies two main effects:

1. **Bit Depth Reduction**: Reduces the number of bits used to represent each sample, creating quantization noise and that characteristic "digital" sound
2. **Sample Rate Reduction**: Uses sample-and-hold to simulate lower sample rates, creating aliasing artifacts

These effects combined produce the distinctive lo-fi, crunchy sound associated with vintage game consoles and chiptune music.

## License

MIT
