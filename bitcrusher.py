#!/usr/bin/env python3
"""
Bitcrusher GUI - A GNOME application for applying bitcrusher effects to WAV files
"""

import gi
import subprocess
import os
import sys
from pathlib import Path

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gio, GLib

class BitcrusherWindow(Adw.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_title("Bitcrusher")
        self.set_default_size(600, 700)

        # Main container
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        # Header bar
        header = Adw.HeaderBar()
        self.main_box.append(header)

        # Content area with margins
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        content.set_margin_top(20)
        content.set_margin_bottom(20)
        content.set_margin_start(20)
        content.set_margin_end(20)

        # Input file section
        input_group = Adw.PreferencesGroup()
        input_group.set_title("Input File")

        self.input_row = Adw.ActionRow()
        self.input_row.set_title("Select WAV file")
        self.input_row.set_subtitle("No file selected")

        input_button = Gtk.Button(label="Browse")
        input_button.set_valign(Gtk.Align.CENTER)
        input_button.connect("clicked", self.on_input_file_clicked)
        self.input_row.add_suffix(input_button)

        input_group.add(self.input_row)
        content.append(input_group)

        # Preset section
        preset_group = Adw.PreferencesGroup()
        preset_group.set_title("Effect Preset")
        preset_group.set_description("Choose a classic console/computer preset or use custom settings")

        preset_row = Adw.ComboRow()
        preset_row.set_title("Preset")

        # Create preset list
        self.presets = Gtk.StringList()
        self.preset_values = ["custom", "gameboy", "nes", "sega", "snes", "c64", "atari", "mild", "heavy", "extreme"]
        preset_names = [
            "Custom Settings",
            "Game Boy",
            "Nintendo NES",
            "Sega Genesis",
            "Super Nintendo",
            "Commodore 64",
            "Atari 2600",
            "Mild Crunch",
            "Heavy Crush",
            "Extreme"
        ]

        for name in preset_names:
            self.presets.append(name)

        preset_row.set_model(self.presets)
        preset_row.set_selected(0)
        preset_row.connect("notify::selected", self.on_preset_changed)
        self.preset_row = preset_row

        preset_group.add(preset_row)
        content.append(preset_group)

        # Custom parameters section
        self.params_group = Adw.PreferencesGroup()
        self.params_group.set_title("Custom Parameters")

        # Bit depth
        self.bit_depth_row = Adw.SpinRow()
        self.bit_depth_row.set_title("Bit Depth")
        self.bit_depth_row.set_subtitle("Lower values = more lo-fi sound (1-16)")
        adjustment = Gtk.Adjustment(value=8, lower=1, upper=16, step_increment=1)
        self.bit_depth_row.set_adjustment(adjustment)
        self.bit_depth_row.set_digits(0)
        self.params_group.add(self.bit_depth_row)

        # Sample rate reduction
        self.sample_rate_row = Adw.SpinRow()
        self.sample_rate_row.set_title("Sample Rate Reduction")
        self.sample_rate_row.set_subtitle("Higher values = more aliasing (1-32)")
        adjustment = Gtk.Adjustment(value=4, lower=1, upper=32, step_increment=1)
        self.sample_rate_row.set_adjustment(adjustment)
        self.sample_rate_row.set_digits(0)
        self.params_group.add(self.sample_rate_row)

        # Mix
        self.mix_row = Adw.SpinRow()
        self.mix_row.set_title("Wet/Dry Mix")
        self.mix_row.set_subtitle("0.0 = original, 1.0 = fully crushed")
        adjustment = Gtk.Adjustment(value=1.0, lower=0.0, upper=1.0, step_increment=0.1)
        self.mix_row.set_adjustment(adjustment)
        self.mix_row.set_digits(1)
        self.params_group.add(self.mix_row)

        content.append(self.params_group)

        # Output section
        output_group = Adw.PreferencesGroup()
        output_group.set_title("Output")

        self.output_row = Adw.ActionRow()
        self.output_row.set_title("Output file")
        self.output_row.set_subtitle("Auto-generated from input filename")

        output_button = Gtk.Button(label="Change")
        output_button.set_valign(Gtk.Align.CENTER)
        output_button.connect("clicked", self.on_output_file_clicked)
        self.output_row.add_suffix(output_button)

        output_group.add(self.output_row)
        content.append(output_group)

        # Process button
        self.process_button = Gtk.Button(label="Process Audio")
        self.process_button.add_css_class("suggested-action")
        self.process_button.add_css_class("pill")
        self.process_button.set_sensitive(False)
        self.process_button.connect("clicked", self.on_process_clicked)
        self.process_button.set_margin_top(10)
        content.append(self.process_button)

        # Status label
        self.status_label = Gtk.Label(label="")
        self.status_label.set_wrap(True)
        self.status_label.set_margin_top(10)
        content.append(self.status_label)

        # Scroll window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_child(content)
        scrolled.set_vexpand(True)

        self.main_box.append(scrolled)
        self.set_content(self.main_box)

        # State
        self.input_file = None
        self.output_file = None

    def on_preset_changed(self, combo_row, param):
        selected = combo_row.get_selected()
        if selected == 0:  # Custom
            self.params_group.set_sensitive(True)
        else:
            self.params_group.set_sensitive(False)

    def on_input_file_clicked(self, button):
        dialog = Gtk.FileDialog()

        # Add WAV filter
        wav_filter = Gtk.FileFilter()
        wav_filter.set_name("WAV files")
        wav_filter.add_pattern("*.wav")
        wav_filter.add_pattern("*.WAV")

        all_filter = Gtk.FileFilter()
        all_filter.set_name("All files")
        all_filter.add_pattern("*")

        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(wav_filter)
        filters.append(all_filter)
        dialog.set_filters(filters)
        dialog.set_default_filter(wav_filter)

        dialog.open(self, None, self.on_input_file_selected)

    def on_input_file_selected(self, dialog, result):
        try:
            file = dialog.open_finish(result)
            if file:
                self.input_file = file.get_path()
                self.input_row.set_subtitle(os.path.basename(self.input_file))

                # Auto-generate output filename
                path = Path(self.input_file)
                self.output_file = str(path.parent / f"{path.stem}_crushed{path.suffix}")
                self.output_row.set_subtitle(os.path.basename(self.output_file))

                self.process_button.set_sensitive(True)
        except Exception as e:
            print(f"Error selecting file: {e}")

    def on_output_file_clicked(self, button):
        dialog = Gtk.FileDialog()
        dialog.set_initial_name("output_crushed.wav")

        # Add WAV filter
        wav_filter = Gtk.FileFilter()
        wav_filter.set_name("WAV files")
        wav_filter.add_pattern("*.wav")

        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(wav_filter)
        dialog.set_filters(filters)

        dialog.save(self, None, self.on_output_file_selected)

    def on_output_file_selected(self, dialog, result):
        try:
            file = dialog.save_finish(result)
            if file:
                self.output_file = file.get_path()
                self.output_row.set_subtitle(os.path.basename(self.output_file))
        except Exception as e:
            print(f"Error selecting output file: {e}")

    def on_process_clicked(self, button):
        if not self.input_file:
            self.show_error("Please select an input file")
            return

        # Disable button during processing
        self.process_button.set_sensitive(False)
        self.status_label.set_text("Processing...")

        # Build command
        script_dir = Path(__file__).parent
        node_cmd = ["node", str(script_dir / "index.js"), "process", self.input_file, self.output_file]

        # Add preset or custom parameters
        selected = self.preset_row.get_selected()
        if selected == 0:  # Custom
            node_cmd.extend(["-b", str(int(self.bit_depth_row.get_value()))])
            node_cmd.extend(["-s", str(int(self.sample_rate_row.get_value()))])
            node_cmd.extend(["-m", str(self.mix_row.get_value())])
        else:
            preset = self.preset_values[selected]
            node_cmd.extend(["-p", preset])

        # Run process in background
        try:
            result = subprocess.run(node_cmd, capture_output=True, text=True, cwd=str(script_dir))

            if result.returncode == 0:
                self.status_label.set_text(f"✓ Success! Saved to: {os.path.basename(self.output_file)}")
            else:
                error_msg = result.stderr if result.stderr else result.stdout
                self.status_label.set_text(f"✗ Error: {error_msg}")
        except Exception as e:
            self.status_label.set_text(f"✗ Error: {str(e)}")
        finally:
            self.process_button.set_sensitive(True)

    def show_error(self, message):
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading("Error")
        dialog.set_body(message)
        dialog.add_response("ok", "OK")
        dialog.present()


class BitcrusherApplication(Adw.Application):
    def __init__(self):
        super().__init__(application_id='com.github.bitcrusher',
                         flags=Gio.ApplicationFlags.FLAGS_NONE)

    def do_activate(self):
        win = self.get_active_window()
        if not win:
            win = BitcrusherWindow(application=self)
        win.present()


def main():
    app = BitcrusherApplication()
    return app.run(sys.argv)


if __name__ == '__main__':
    main()
