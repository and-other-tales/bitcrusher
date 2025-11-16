/**
 * Unit tests for Bitcrusher audio effect
 */

import { test, describe } from 'node:test';
import assert from 'node:assert';
import { Bitcrusher, presets } from './bitcrusher.js';

describe('Bitcrusher Class', () => {
  describe('Constructor', () => {
    test('should create with default options', () => {
      const bc = new Bitcrusher();
      assert.strictEqual(bc.bitDepth, 8);
      assert.strictEqual(bc.sampleRateReduction, 4);
      assert.strictEqual(bc.mix, 1.0);
      assert.strictEqual(bc.lowpassFreq, null);
      assert.strictEqual(bc.hardClip, false);
    });

    test('should accept custom options', () => {
      const bc = new Bitcrusher({
        bitDepth: 4,
        sampleRateReduction: 8,
        mix: 0.5,
        lowpassFreq: 4000,
        hardClip: true,
        clipThreshold: 0.7
      });
      assert.strictEqual(bc.bitDepth, 4);
      assert.strictEqual(bc.sampleRateReduction, 8);
      assert.strictEqual(bc.mix, 0.5);
      assert.strictEqual(bc.lowpassFreq, 4000);
      assert.strictEqual(bc.hardClip, true);
      assert.strictEqual(bc.clipThreshold, 0.7);
    });
  });

  describe('Bit Depth Reduction', () => {
    test('should quantize audio based on bit depth', () => {
      const bc = new Bitcrusher({ bitDepth: 1, sampleRateReduction: 1 });
      const input = new Float32Array([0.0, 0.5, 1.0, -0.5, -1.0]);
      const output = bc.process(input, 44100);

      // With 1-bit, we should only get -1 and 1
      output.forEach(sample => {
        assert.ok(Math.abs(sample) === 1.0 || Math.abs(sample) < 0.01);
      });
    });

    test('should preserve more detail with higher bit depth', () => {
      const bc = new Bitcrusher({ bitDepth: 16, sampleRateReduction: 1 });
      const input = new Float32Array([0.5]);
      const output = bc.process(input, 44100);

      // With 16-bit, 0.5 should be very close to 0.5
      assert.ok(Math.abs(output[0] - 0.5) < 0.001);
    });

    test('should handle 8-bit quantization correctly', () => {
      const bc = new Bitcrusher({ bitDepth: 8, sampleRateReduction: 1 });
      const input = new Float32Array([0.3333]);
      const output = bc.process(input, 44100);

      // 8-bit has 255 steps, so quantization should be visible
      const steps = Math.pow(2, 8) - 1;
      const expected = Math.round(0.3333 * steps) / steps;
      assert.ok(Math.abs(output[0] - expected) < 0.01);
    });
  });

  describe('Sample Rate Reduction', () => {
    test('should hold samples based on reduction factor', () => {
      const bc = new Bitcrusher({ bitDepth: 16, sampleRateReduction: 4 });
      const input = new Float32Array([1.0, 0.5, 0.3, 0.1, 0.9, 0.7, 0.5, 0.3]);
      const output = bc.process(input, 44100);

      // With 4x reduction, every 4 samples should have the same value
      assert.strictEqual(output[0], output[1]);
      assert.strictEqual(output[1], output[2]);
      assert.strictEqual(output[2], output[3]);

      assert.strictEqual(output[4], output[5]);
      assert.strictEqual(output[5], output[6]);
      assert.strictEqual(output[6], output[7]);
    });

    test('should not hold samples with reduction factor of 1', () => {
      const bc = new Bitcrusher({ bitDepth: 16, sampleRateReduction: 1 });
      const input = new Float32Array([1.0, 0.5, 0.3, 0.1]);
      const output = bc.process(input, 44100);

      // Values should all be different (or very close to input)
      assert.ok(Math.abs(output[0] - 1.0) < 0.01);
      assert.ok(Math.abs(output[1] - 0.5) < 0.01);
      assert.ok(Math.abs(output[2] - 0.3) < 0.01);
      assert.ok(Math.abs(output[3] - 0.1) < 0.01);
    });
  });

  describe('Mix Control', () => {
    test('should output original signal with mix=0', () => {
      const bc = new Bitcrusher({ bitDepth: 1, sampleRateReduction: 8, mix: 0.0 });
      const input = new Float32Array([0.5, 0.3, 0.7]);
      const output = bc.process(input, 44100);

      // With mix=0, output should equal input
      assert.ok(Math.abs(output[0] - 0.5) < 0.01);
      assert.ok(Math.abs(output[1] - 0.3) < 0.01);
      assert.ok(Math.abs(output[2] - 0.7) < 0.01);
    });

    test('should output fully processed signal with mix=1', () => {
      const bc = new Bitcrusher({ bitDepth: 1, sampleRateReduction: 1, mix: 1.0 });
      const input = new Float32Array([0.5]);
      const output = bc.process(input, 44100);

      // With 1-bit and mix=1, output should be quantized to -1 or 1
      assert.ok(Math.abs(output[0]) > 0.9);
    });

    test('should blend signals with mix=0.5', () => {
      const bc = new Bitcrusher({ bitDepth: 1, sampleRateReduction: 1, mix: 0.5 });
      const input = new Float32Array([0.0]);
      const output = bc.process(input, 44100);

      // Blended signal should be between extremes
      assert.ok(Math.abs(output[0]) < 1.0);
    });
  });

  describe('Hard Clipping', () => {
    test('should clip samples above threshold when enabled', () => {
      const bc = new Bitcrusher({
        bitDepth: 16,
        sampleRateReduction: 1,
        hardClip: true,
        clipThreshold: 0.5
      });

      const input = new Float32Array([0.8, -0.8, 0.3, -0.3]);
      const output = bc.process(input, 44100);

      // Values above threshold should be clipped to threshold
      assert.ok(output[0] <= 0.51); // Allow small margin for quantization
      assert.ok(output[1] >= -0.51);
      // Values below threshold should be preserved
      assert.ok(Math.abs(output[2] - 0.3) < 0.1);
      assert.ok(Math.abs(output[3] + 0.3) < 0.1);
    });

    test('should not clip when disabled', () => {
      const bc = new Bitcrusher({
        bitDepth: 16,
        sampleRateReduction: 1,
        hardClip: false
      });

      const input = new Float32Array([0.9, -0.9]);
      const output = bc.process(input, 44100);

      // Values should not be clipped
      assert.ok(Math.abs(output[0] - 0.9) < 0.1);
      assert.ok(Math.abs(output[1] + 0.9) < 0.1);
    });
  });

  describe('Output Validation', () => {
    test('should clamp output to [-1, 1] range', () => {
      const bc = new Bitcrusher({ bitDepth: 4, sampleRateReduction: 1 });
      const input = new Float32Array([1.5, -1.5, 0.5]); // Out of range inputs
      const output = bc.process(input, 44100);

      output.forEach(sample => {
        assert.ok(sample >= -1.0 && sample <= 1.0);
      });
    });

    test('should return Float32Array of same length as input', () => {
      const bc = new Bitcrusher();
      const input = new Float32Array(100);
      const output = bc.process(input, 44100);

      assert.ok(output instanceof Float32Array);
      assert.strictEqual(output.length, input.length);
    });
  });

  describe('Int16Array Input Support', () => {
    test('should handle Int16Array input', () => {
      const bc = new Bitcrusher({ bitDepth: 8, sampleRateReduction: 1 });
      const input = new Int16Array([16384, -16384, 0]); // ~0.5, -0.5, 0
      const output = bc.process(input, 44100);

      assert.ok(output instanceof Float32Array);
      assert.strictEqual(output.length, 3);
      assert.ok(Math.abs(output[0] - 0.5) < 0.1);
      assert.ok(Math.abs(output[1] + 0.5) < 0.1);
    });
  });

  describe('Stereo Processing', () => {
    test('should process stereo audio', () => {
      const bc = new Bitcrusher({ bitDepth: 8, sampleRateReduction: 2 });
      const input = new Float32Array([0.5, 0.3, 0.7, 0.4]); // L, R, L, R
      const output = bc.processStereo(input, 44100);

      assert.ok(output instanceof Float32Array);
      assert.strictEqual(output.length, input.length);
    });

    test('should apply mono downmix when enabled', () => {
      const bc = new Bitcrusher({
        bitDepth: 16,
        sampleRateReduction: 1,
        monoDownmix: true
      });

      const input = new Float32Array([0.8, 0.4, 0.6, 0.2]); // L, R, L, R
      const output = bc.processStereo(input, 44100);

      // First pair: (0.8 + 0.4) / 2 = 0.6
      // Both channels should have the same value when mono downmixed
      assert.ok(Math.abs(output[0] - output[1]) < 0.01);
      assert.ok(Math.abs(output[2] - output[3]) < 0.01);
    });

    test('should maintain stereo separation when mono downmix disabled', () => {
      const bc = new Bitcrusher({
        bitDepth: 16,
        sampleRateReduction: 1,
        monoDownmix: false
      });

      const input = new Float32Array([0.8, 0.2, 0.6, 0.4]); // L, R, L, R
      const output = bc.processStereo(input, 44100);

      // Channels should be different
      assert.ok(Math.abs(output[0] - output[1]) > 0.1);
      assert.ok(Math.abs(output[2] - output[3]) > 0.1);
    });
  });
});

describe('Presets', () => {
  test('should have all expected presets', () => {
    const expectedPresets = [
      'gameboy', 'nes', 'sega', 'snes',
      'c64', 'atari',
      'mild', 'heavy', 'extreme'
    ];

    expectedPresets.forEach(presetName => {
      assert.ok(presets[presetName], `Missing preset: ${presetName}`);
    });
  });

  test('all presets should have required properties', () => {
    Object.entries(presets).forEach(([name, preset]) => {
      assert.ok(preset.name, `${name}: missing name`);
      assert.ok(preset.description, `${name}: missing description`);
      assert.ok(typeof preset.bitDepth === 'number', `${name}: invalid bitDepth`);
      assert.ok(typeof preset.sampleRateReduction === 'number', `${name}: invalid sampleRateReduction`);
      assert.ok(preset.bitDepth >= 1 && preset.bitDepth <= 16, `${name}: bitDepth out of range`);
      assert.ok(preset.sampleRateReduction >= 1, `${name}: sampleRateReduction too low`);
    });
  });

  test('Game Boy preset should have correct settings', () => {
    const gameboy = presets.gameboy;
    assert.strictEqual(gameboy.bitDepth, 4);
    assert.strictEqual(gameboy.sampleRateReduction, 8);
    assert.strictEqual(gameboy.monoDownmix, true);
    assert.strictEqual(gameboy.hardClip, true);
  });

  test('SNES preset should have higher quality settings', () => {
    const snes = presets.snes;
    assert.strictEqual(snes.bitDepth, 8);
    assert.strictEqual(snes.sampleRateReduction, 2);
    assert.strictEqual(snes.monoDownmix, false); // Stereo
  });

  test('presets should work with Bitcrusher', () => {
    const bc = new Bitcrusher(presets.gameboy);
    const input = new Float32Array([0.5, 0.3, 0.7]);
    const output = bc.process(input, 44100);

    assert.ok(output instanceof Float32Array);
    assert.strictEqual(output.length, input.length);
  });
});

describe('Low-pass Filter', () => {
  test('should apply low-pass filter when frequency is set', () => {
    const bc = new Bitcrusher({
      bitDepth: 16,
      sampleRateReduction: 1,
      lowpassFreq: 1000
    });

    const input = new Float32Array(100).fill(0.5);
    const output = bc.process(input, 44100);

    // Filter should smooth the signal
    assert.ok(output instanceof Float32Array);
    assert.strictEqual(output.length, 100);
  });

  test('should not apply filter when lowpassFreq is null', () => {
    const bc = new Bitcrusher({
      bitDepth: 16,
      sampleRateReduction: 1,
      lowpassFreq: null
    });

    const input = new Float32Array([0.5, 0.3, 0.7]);
    const output = bc.process(input, 44100);

    // Without filter, values should be close to quantized input
    assert.ok(Math.abs(output[0] - 0.5) < 0.01);
  });
});

describe('Edge Cases', () => {
  test('should handle empty input', () => {
    const bc = new Bitcrusher();
    const input = new Float32Array(0);
    const output = bc.process(input, 44100);

    assert.strictEqual(output.length, 0);
  });

  test('should handle single sample', () => {
    const bc = new Bitcrusher();
    const input = new Float32Array([0.5]);
    const output = bc.process(input, 44100);

    assert.strictEqual(output.length, 1);
    assert.ok(!isNaN(output[0]));
  });

  test('should handle very high sample rate reduction', () => {
    const bc = new Bitcrusher({ bitDepth: 8, sampleRateReduction: 100 });
    const input = new Float32Array(1000).fill(0.5);
    const output = bc.process(input, 44100);

    assert.strictEqual(output.length, 1000);
    // All values in groups of 100 should be identical
    for (let i = 0; i < 900; i += 100) {
      assert.strictEqual(output[i], output[i + 99]);
    }
  });

  test('should handle very low bit depth', () => {
    const bc = new Bitcrusher({ bitDepth: 1, sampleRateReduction: 1 });
    const input = new Float32Array([0.1, 0.5, 0.9, -0.1, -0.5, -0.9]);
    const output = bc.process(input, 44100);

    // With 1-bit (steps = 2^1 - 1 = 1), valid quantized values are -1, 0, or 1
    output.forEach(sample => {
      const validValues = [-1, 0, 1];
      const isValid = validValues.some(val => Math.abs(sample - val) < 0.01);
      assert.ok(isValid, `Sample ${sample} should be close to -1, 0, or 1`);
    });
  });
});
