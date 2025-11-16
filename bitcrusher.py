#!/usr/bin/env python3
"""
Bitcrusher GUI - A GNOME application for applying bitcrusher effects to WAV files
"""

import gi
import subprocess
import os
import sys
import struct
import wave
from pathlib import Path

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('Gst', '1.0')

from gi.repository import Gtk, Adw, Gio, GLib, Gst

# Initialize GStreamer
Gst.init(None)


class WaveformWidget(Gtk.DrawingArea):
    """Custom widget to draw audio waveform"""
    def __init__(self):
        super().__init__()
        self.waveform_data = None
        self.playback_position = 0.0  # 0.0 to 1.0
        self.set_content_height(120)
        self.set_draw_func(self.on_draw)

    def set_waveform(self, samples):
        """Set waveform data from audio samples"""
        if samples is None or len(samples) == 0:
            self.waveform_data = None
        else:
            # Downsample for display (max 2000 points)
            target_points = 2000
            step = max(1, len(samples) // target_points)

            # Calculate min/max for each segment
            downsampled = []
            for i in range(0, len(samples), step):
                segment = samples[i:i+step]
                if len(segment) > 0:
                    downsampled.append((min(segment), max(segment)))

            self.waveform_data = downsampled

        self.queue_draw()

    def set_playback_position(self, position):
        """Set playback position (0.0 to 1.0)"""
        self.playback_position = max(0.0, min(1.0, position))
        self.queue_draw()

    def on_draw(self, area, cr, width, height):
        """Draw the waveform"""
        # Background
        cr.set_source_rgb(0.95, 0.95, 0.95)
        cr.rectangle(0, 0, width, height)
        cr.fill()

        if not self.waveform_data:
            # Draw placeholder text
            cr.set_source_rgb(0.5, 0.5, 0.5)
            cr.select_font_face("Sans", 0, 0)
            cr.set_font_size(14)
            text = "No audio loaded"
            extents = cr.text_extents(text)
            cr.move_to((width - extents.width) / 2, (height + extents.height) / 2)
            cr.show_text(text)
            return

        # Draw waveform
        center_y = height / 2
        scale_y = height / 2 * 0.9  # Leave some margin

        cr.set_source_rgb(0.2, 0.6, 0.8)
        cr.set_line_width(1)

        points_per_pixel = len(self.waveform_data) / width

        for x in range(width):
            idx = int(x * points_per_pixel)
            if idx < len(self.waveform_data):
                min_val, max_val = self.waveform_data[idx]

                y1 = center_y - (min_val * scale_y)
                y2 = center_y - (max_val * scale_y)

                cr.move_to(x, y1)
                cr.line_to(x, y2)
                cr.stroke()

        # Draw playback position line
        if self.playback_position > 0:
            position_x = width * self.playback_position
            cr.set_source_rgba(1, 0, 0, 0.7)
            cr.set_line_width(2)
            cr.move_to(position_x, 0)
            cr.line_to(position_x, height)
            cr.stroke()


class BitcrusherWindow(Adw.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_title("Bitcrusher")
        self.set_default_size(600, 950)

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

        # Preview section
        preview_group = Adw.PreferencesGroup()
        preview_group.set_title("Audio Preview")
        preview_group.set_description("Visualize and compare original vs. processed audio")

        # Original waveform
        original_label = Gtk.Label(label="Original")
        original_label.set_xalign(0)
        original_label.set_margin_top(5)
        preview_group.add(original_label)

        self.original_waveform = WaveformWidget()
        preview_group.add(self.original_waveform)

        # Original playback controls
        original_controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        original_controls.set_margin_top(5)
        original_controls.set_margin_bottom(10)

        self.original_play_btn = Gtk.Button(icon_name="media-playback-start-symbolic")
        self.original_play_btn.set_sensitive(False)
        self.original_play_btn.connect("clicked", lambda b: self.toggle_playback("original"))
        original_controls.append(self.original_play_btn)

        self.original_stop_btn = Gtk.Button(icon_name="media-playback-stop-symbolic")
        self.original_stop_btn.set_sensitive(False)
        self.original_stop_btn.connect("clicked", lambda b: self.stop_playback("original"))
        original_controls.append(self.original_stop_btn)

        self.original_time_label = Gtk.Label(label="0:00 / 0:00")
        self.original_time_label.set_margin_start(10)
        original_controls.append(self.original_time_label)

        preview_group.add(original_controls)

        # Processed waveform
        processed_label = Gtk.Label(label="Processed")
        processed_label.set_xalign(0)
        processed_label.set_margin_top(15)
        preview_group.add(processed_label)

        self.processed_waveform = WaveformWidget()
        preview_group.add(self.processed_waveform)

        # Processed playback controls
        processed_controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        processed_controls.set_margin_top(5)

        self.processed_play_btn = Gtk.Button(icon_name="media-playback-start-symbolic")
        self.processed_play_btn.set_sensitive(False)
        self.processed_play_btn.connect("clicked", lambda b: self.toggle_playback("processed"))
        processed_controls.append(self.processed_play_btn)

        self.processed_stop_btn = Gtk.Button(icon_name="media-playback-stop-symbolic")
        self.processed_stop_btn.set_sensitive(False)
        self.processed_stop_btn.connect("clicked", lambda b: self.stop_playback("processed"))
        processed_controls.append(self.processed_stop_btn)

        self.processed_time_label = Gtk.Label(label="0:00 / 0:00")
        self.processed_time_label.set_margin_start(10)
        processed_controls.append(self.processed_time_label)

        preview_group.add(processed_controls)

        content.append(preview_group)

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

        # Progress bar
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_margin_top(10)
        self.progress_bar.set_show_text(True)
        self.progress_bar.set_visible(False)
        content.append(self.progress_bar)

        # Status text view for detailed output
        self.status_frame = Gtk.Frame()
        self.status_frame.set_margin_top(10)
        self.status_frame.set_visible(False)

        status_scroll = Gtk.ScrolledWindow()
        status_scroll.set_min_content_height(150)
        status_scroll.set_max_content_height(200)

        self.status_buffer = Gtk.TextBuffer()
        self.status_view = Gtk.TextView()
        self.status_view.set_buffer(self.status_buffer)
        self.status_view.set_editable(False)
        self.status_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.status_view.set_margin_top(5)
        self.status_view.set_margin_bottom(5)
        self.status_view.set_margin_start(5)
        self.status_view.set_margin_end(5)

        status_scroll.set_child(self.status_view)
        self.status_frame.set_child(status_scroll)
        content.append(self.status_frame)

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
        self.process = None
        self.process_watch_id = None

        # Audio players
        self.original_player = None
        self.processed_player = None
        self.original_duration = 0
        self.processed_duration = 0
        self.update_position_id = None

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

                # Load waveform and setup player
                samples, duration = self.load_waveform(self.input_file)
                if samples:
                    self.original_waveform.set_waveform(samples)
                    self.setup_player(self.input_file, "original")
                    self.original_play_btn.set_sensitive(True)
                    self.original_stop_btn.set_sensitive(True)
                    self.update_time_label("original", 0)

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

        # Show progress UI
        self.progress_bar.set_visible(True)
        self.progress_bar.set_fraction(0.0)
        self.progress_bar.set_text("Starting...")
        self.status_frame.set_visible(True)
        self.status_buffer.set_text("")
        self.status_label.set_text("")

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

        # Run process asynchronously
        try:
            self.process = subprocess.Popen(
                node_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                cwd=str(script_dir)
            )

            # Watch stdout for updates
            GLib.io_add_watch(
                self.process.stdout,
                GLib.IO_IN | GLib.IO_HUP,
                self.on_process_output
            )

            # Watch stderr for errors
            GLib.io_add_watch(
                self.process.stderr,
                GLib.IO_IN | GLib.IO_HUP,
                self.on_process_error
            )

            # Check process completion
            GLib.timeout_add(100, self.check_process_completion)

        except Exception as e:
            self.append_status(f"✗ Error starting process: {str(e)}\n")
            self.finish_processing(False)

    def on_process_output(self, source, condition):
        """Handle stdout output from the processing subprocess"""
        if condition == GLib.IO_HUP:
            return False

        line = source.readline()
        if line:
            self.append_status(line)
            self.update_progress_from_output(line)

        return True

    def on_process_error(self, source, condition):
        """Handle stderr output from the processing subprocess"""
        if condition == GLib.IO_HUP:
            return False

        line = source.readline()
        if line:
            self.append_status(f"⚠ {line}")

        return True

    def append_status(self, text):
        """Append text to the status buffer"""
        end_iter = self.status_buffer.get_end_iter()
        self.status_buffer.insert(end_iter, text)

        # Auto-scroll to bottom
        mark = self.status_buffer.create_mark(None, end_iter, False)
        self.status_view.scroll_to_mark(mark, 0.0, True, 0.0, 1.0)

    def update_progress_from_output(self, line):
        """Update progress bar based on output text"""
        line = line.strip()

        if "Reading:" in line:
            self.progress_bar.set_fraction(0.1)
            self.progress_bar.set_text("Reading input file...")
        elif "Sample Rate:" in line or "Channels:" in line:
            self.progress_bar.set_fraction(0.2)
            self.progress_bar.set_text("Analyzing audio...")
        elif "Applying bitcrusher effect:" in line:
            self.progress_bar.set_fraction(0.3)
            self.progress_bar.set_text("Applying effect...")
        elif "Normalizing output" in line:
            self.progress_bar.set_fraction(0.8)
            self.progress_bar.set_text("Normalizing...")
        elif "Output saved to:" in line:
            self.progress_bar.set_fraction(1.0)
            self.progress_bar.set_text("Complete!")

    def check_process_completion(self):
        """Check if the process has completed"""
        if self.process is None:
            return False

        returncode = self.process.poll()

        if returncode is not None:
            # Process has finished
            success = returncode == 0

            if success:
                self.status_label.set_text(f"✓ Success! Saved to: {os.path.basename(self.output_file)}")
            else:
                self.status_label.set_text(f"✗ Processing failed with exit code {returncode}")

            self.finish_processing(success)
            return False

        # Keep checking
        return True

    def finish_processing(self, success):
        """Clean up after processing completes"""
        self.process = None
        self.process_button.set_sensitive(True)

        if not success:
            self.progress_bar.set_text("Failed")
            self.progress_bar.add_css_class("error")
        else:
            # Load processed waveform and setup player
            if self.output_file and os.path.exists(self.output_file):
                samples, duration = self.load_waveform(self.output_file)
                if samples:
                    self.processed_waveform.set_waveform(samples)
                    self.setup_player(self.output_file, "processed")
                    self.processed_play_btn.set_sensitive(True)
                    self.processed_stop_btn.set_sensitive(True)
                    self.update_time_label("processed", 0)

    def load_waveform(self, filepath):
        """Load waveform data from a WAV file"""
        try:
            with wave.open(filepath, 'rb') as wf:
                n_channels = wf.getnchannels()
                sample_width = wf.getsampwidth()
                n_frames = wf.getnframes()
                framerate = wf.getframerate()

                # Read all frames
                frames = wf.readframes(n_frames)

                # Convert to samples
                if sample_width == 1:
                    samples = struct.unpack(f"{n_frames * n_channels}B", frames)
                    samples = [(s - 128) / 128.0 for s in samples]
                elif sample_width == 2:
                    samples = struct.unpack(f"{n_frames * n_channels}h", frames)
                    samples = [s / 32768.0 for s in samples]
                else:
                    return None, 0

                # Mix to mono for display
                if n_channels == 2:
                    mono = [(samples[i] + samples[i+1]) / 2 for i in range(0, len(samples), 2)]
                    samples = mono

                duration = n_frames / framerate
                return samples, duration

        except Exception as e:
            print(f"Error loading waveform: {e}")
            return None, 0

    def setup_player(self, filepath, player_type):
        """Setup GStreamer player for a file"""
        # Clean up existing player
        if player_type == "original" and self.original_player:
            self.original_player.set_state(Gst.State.NULL)
        elif player_type == "processed" and self.processed_player:
            self.processed_player.set_state(Gst.State.NULL)

        # Create new player
        player = Gst.ElementFactory.make("playbin", None)
        player.set_property("uri", f"file://{filepath}")

        # Get duration
        player.set_state(Gst.State.PAUSED)
        player.get_state(Gst.CLOCK_TIME_NONE)

        success, duration = player.query_duration(Gst.Format.TIME)
        duration_sec = duration / Gst.SECOND if success else 0

        # Reset to ready
        player.set_state(Gst.State.READY)

        if player_type == "original":
            self.original_player = player
            self.original_duration = duration_sec
        else:
            self.processed_player = player
            self.processed_duration = duration_sec

        return player

    def toggle_playback(self, player_type):
        """Toggle play/pause for a player"""
        if player_type == "original":
            player = self.original_player
            play_btn = self.original_play_btn
        else:
            player = self.processed_player
            play_btn = self.processed_play_btn

        if not player:
            return

        state = player.get_state(0)[1]

        if state == Gst.State.PLAYING:
            # Pause
            player.set_state(Gst.State.PAUSED)
            play_btn.set_icon_name("media-playback-start-symbolic")
            if self.update_position_id:
                GLib.source_remove(self.update_position_id)
                self.update_position_id = None
        else:
            # Play
            player.set_state(Gst.State.PLAYING)
            play_btn.set_icon_name("media-playback-pause-symbolic")

            # Start position updates
            if not self.update_position_id:
                self.update_position_id = GLib.timeout_add(100, self.update_positions)

    def stop_playback(self, player_type):
        """Stop playback for a player"""
        if player_type == "original":
            player = self.original_player
            play_btn = self.original_play_btn
            waveform = self.original_waveform
        else:
            player = self.processed_player
            play_btn = self.processed_play_btn
            waveform = self.processed_waveform

        if not player:
            return

        player.set_state(Gst.State.READY)
        play_btn.set_icon_name("media-playback-start-symbolic")
        waveform.set_playback_position(0)

        if self.update_position_id:
            GLib.source_remove(self.update_position_id)
            self.update_position_id = None

        self.update_time_label(player_type, 0)

    def update_positions(self):
        """Update playback positions for all active players"""
        active = False

        # Update original player
        if self.original_player:
            state = self.original_player.get_state(0)[1]
            if state == Gst.State.PLAYING:
                active = True
                success, position = self.original_player.query_position(Gst.Format.TIME)
                if success:
                    position_sec = position / Gst.SECOND
                    self.update_time_label("original", position_sec)

                    if self.original_duration > 0:
                        fraction = position_sec / self.original_duration
                        self.original_waveform.set_playback_position(fraction)

                    # Check if finished
                    if position_sec >= self.original_duration:
                        self.stop_playback("original")

        # Update processed player
        if self.processed_player:
            state = self.processed_player.get_state(0)[1]
            if state == Gst.State.PLAYING:
                active = True
                success, position = self.processed_player.query_position(Gst.Format.TIME)
                if success:
                    position_sec = position / Gst.SECOND
                    self.update_time_label("processed", position_sec)

                    if self.processed_duration > 0:
                        fraction = position_sec / self.processed_duration
                        self.processed_waveform.set_playback_position(fraction)

                    # Check if finished
                    if position_sec >= self.processed_duration:
                        self.stop_playback("processed")

        return active  # Continue if any player is active

    def update_time_label(self, player_type, position_sec):
        """Update time label for a player"""
        if player_type == "original":
            duration = self.original_duration
            label = self.original_time_label
        else:
            duration = self.processed_duration
            label = self.processed_time_label

        pos_str = self.format_time(position_sec)
        dur_str = self.format_time(duration)
        label.set_text(f"{pos_str} / {dur_str}")

    def format_time(self, seconds):
        """Format seconds as MM:SS"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"

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
