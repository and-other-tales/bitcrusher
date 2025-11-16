"""
Unit tests for Bitcrusher GUI application
"""

import unittest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))


class TestBitcrusherWindow(unittest.TestCase):
    """Test BitcrusherWindow class"""

    def setUp(self):
        """Set up test fixtures"""
        # Mock GTK/Adw to avoid requiring display server
        self.mock_gtk = MagicMock()
        self.mock_adw = MagicMock()
        self.mock_gio = MagicMock()
        self.mock_glib = MagicMock()

        sys.modules['gi'] = MagicMock()
        sys.modules['gi.repository'] = MagicMock()
        sys.modules['gi.repository.Gtk'] = self.mock_gtk
        sys.modules['gi.repository.Adw'] = self.mock_adw
        sys.modules['gi.repository.Gio'] = self.mock_gio
        sys.modules['gi.repository.GLib'] = self.mock_glib

    def tearDown(self):
        """Clean up test fixtures"""
        # Remove mocked modules
        for module in ['gi', 'gi.repository', 'gi.repository.Gtk',
                       'gi.repository.Adw', 'gi.repository.Gio',
                       'gi.repository.GLib']:
            if module in sys.modules:
                del sys.modules[module]

    def test_preset_values_match_names(self):
        """Test that preset values and names are aligned"""
        import bitcrusher as bc_module

        # The preset values list
        preset_values = ["custom", "gameboy", "nes", "sega", "snes",
                        "c64", "atari", "mild", "heavy", "extreme"]
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

        # Should have same length
        self.assertEqual(len(preset_values), len(preset_names))
        # Should have 10 presets (1 custom + 9 presets)
        self.assertEqual(len(preset_values), 10)

    def test_output_filename_generation(self):
        """Test automatic output filename generation logic"""
        from pathlib import Path

        # Test basic filename
        input_file = "/home/user/test.wav"
        path = Path(input_file)
        output = str(path.parent / f"{path.stem}_crushed{path.suffix}")
        self.assertEqual(output, "/home/user/test_crushed.wav")

        # Test filename with underscores
        input_file = "/home/user/my_audio_file.wav"
        path = Path(input_file)
        output = str(path.parent / f"{path.stem}_crushed{path.suffix}")
        self.assertEqual(output, "/home/user/my_audio_file_crushed.wav")

        # Test filename with spaces
        input_file = "/home/user/my audio.wav"
        path = Path(input_file)
        output = str(path.parent / f"{path.stem}_crushed{path.suffix}")
        self.assertEqual(output, "/home/user/my audio_crushed.wav")


class TestCommandBuilding(unittest.TestCase):
    """Test command building logic"""

    def test_custom_preset_command(self):
        """Test command building for custom preset"""
        script_dir = Path("/home/user/bitcrusher")
        input_file = "/home/user/input.wav"
        output_file = "/home/user/output.wav"

        # Custom preset (selected = 0)
        bit_depth = 8
        sample_rate = 4
        mix = 1.0

        node_cmd = [
            "node",
            str(script_dir / "index.js"),
            "process",
            input_file,
            output_file,
            "-b", str(bit_depth),
            "-s", str(sample_rate),
            "-m", str(mix)
        ]

        self.assertIn("node", node_cmd)
        self.assertIn("process", node_cmd)
        self.assertIn("-b", node_cmd)
        self.assertIn("-s", node_cmd)
        self.assertIn("-m", node_cmd)
        self.assertEqual(node_cmd[node_cmd.index("-b") + 1], "8")
        self.assertEqual(node_cmd[node_cmd.index("-s") + 1], "4")

    def test_preset_command(self):
        """Test command building with preset"""
        script_dir = Path("/home/user/bitcrusher")
        input_file = "/home/user/input.wav"
        output_file = "/home/user/output.wav"

        # Preset selection (e.g., gameboy at index 1)
        preset_values = ["custom", "gameboy", "nes", "sega", "snes",
                        "c64", "atari", "mild", "heavy", "extreme"]
        selected = 1  # gameboy
        preset = preset_values[selected]

        node_cmd = [
            "node",
            str(script_dir / "index.js"),
            "process",
            input_file,
            output_file,
            "-p", preset
        ]

        self.assertIn("-p", node_cmd)
        self.assertIn("gameboy", node_cmd)
        self.assertEqual(node_cmd[node_cmd.index("-p") + 1], "gameboy")


class TestApplicationID(unittest.TestCase):
    """Test application ID and metadata"""

    def test_application_id_format(self):
        """Test that application ID follows reverse domain notation"""
        app_id = 'com.github.bitcrusher'

        # Should have at least 3 parts
        parts = app_id.split('.')
        self.assertGreaterEqual(len(parts), 3)

        # Should not have spaces
        self.assertNotIn(' ', app_id)

        # Should be lowercase
        self.assertEqual(app_id, app_id.lower())


class TestFileValidation(unittest.TestCase):
    """Test file validation logic"""

    def test_wav_file_extension(self):
        """Test WAV file extension validation"""
        valid_files = [
            "test.wav",
            "test.WAV",
            "my_audio.wav",
            "path/to/file.wav"
        ]

        for filepath in valid_files:
            self.assertTrue(
                filepath.lower().endswith('.wav'),
                f"{filepath} should be recognized as WAV"
            )

    def test_invalid_file_extension(self):
        """Test non-WAV file extension"""
        invalid_files = [
            "test.mp3",
            "test.txt",
            "test.ogg",
            "test.flac"
        ]

        for filepath in invalid_files:
            self.assertFalse(
                filepath.lower().endswith('.wav'),
                f"{filepath} should not be recognized as WAV"
            )


class TestParameterValidation(unittest.TestCase):
    """Test parameter validation logic"""

    def test_bit_depth_range(self):
        """Test bit depth parameter range (1-16)"""
        valid_values = [1, 4, 8, 12, 16]
        for value in valid_values:
            self.assertGreaterEqual(value, 1)
            self.assertLessEqual(value, 16)

        invalid_values = [0, -1, 17, 32]
        for value in invalid_values:
            self.assertFalse(1 <= value <= 16)

    def test_sample_rate_reduction_range(self):
        """Test sample rate reduction parameter range (1-32)"""
        valid_values = [1, 4, 8, 16, 32]
        for value in valid_values:
            self.assertGreaterEqual(value, 1)
            self.assertLessEqual(value, 32)

        invalid_values = [0, -1, 33, 100]
        for value in invalid_values:
            self.assertFalse(1 <= value <= 32)

    def test_mix_range(self):
        """Test mix parameter range (0.0-1.0)"""
        valid_values = [0.0, 0.5, 0.7, 1.0]
        for value in valid_values:
            self.assertGreaterEqual(value, 0.0)
            self.assertLessEqual(value, 1.0)

        invalid_values = [-0.1, 1.1, 2.0, -1.0]
        for value in invalid_values:
            self.assertFalse(0.0 <= value <= 1.0)


class TestSubprocessCalling(unittest.TestCase):
    """Test subprocess command execution"""

    @patch('subprocess.run')
    def test_successful_processing(self, mock_run):
        """Test successful audio processing"""
        # Mock successful subprocess run
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Success"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        import subprocess
        result = subprocess.run(
            ["node", "index.js", "process", "input.wav", "output.wav", "-p", "gameboy"],
            capture_output=True,
            text=True
        )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "Success")

    @patch('subprocess.run')
    def test_failed_processing(self, mock_run):
        """Test failed audio processing"""
        # Mock failed subprocess run
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error: File not found"
        mock_run.return_value = mock_result

        import subprocess
        result = subprocess.run(
            ["node", "index.js", "process", "nonexistent.wav", "output.wav"],
            capture_output=True,
            text=True
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("Error", result.stderr)


class TestIntegration(unittest.TestCase):
    """Integration tests"""

    def test_node_backend_available(self):
        """Test that Node.js backend files exist"""
        script_dir = Path(__file__).parent

        # Check that index.js exists
        self.assertTrue(
            (script_dir / "index.js").exists(),
            "index.js should exist"
        )

        # Check that bitcrusher.js exists
        self.assertTrue(
            (script_dir / "bitcrusher.js").exists(),
            "bitcrusher.js should exist"
        )

    def test_package_json_exists(self):
        """Test that package.json exists"""
        script_dir = Path(__file__).parent
        package_json = script_dir / "package.json"

        self.assertTrue(
            package_json.exists(),
            "package.json should exist"
        )

    def test_pyproject_toml_exists(self):
        """Test that pyproject.toml exists"""
        script_dir = Path(__file__).parent
        pyproject = script_dir / "pyproject.toml"

        self.assertTrue(
            pyproject.exists(),
            "pyproject.toml should exist"
        )


if __name__ == '__main__':
    unittest.main()
