/**
 * Bitcrusher audio effect for creating chiptune-style sounds
 */

export class Bitcrusher {
  constructor(options = {}) {
    this.bitDepth = options.bitDepth || 8;
    this.sampleRateReduction = options.sampleRateReduction || 4;
    this.mix = options.mix !== undefined ? options.mix : 1.0;
    this.lowpassFreq = options.lowpassFreq || null; // Low-pass filter cutoff frequency
    this.hardClip = options.hardClip !== undefined ? options.hardClip : false;
    this.clipThreshold = options.clipThreshold || 0.8;
    this.monoDownmix = options.monoDownmix || false;

    // Low-pass filter state (simple one-pole filter)
    this.filterStateL = 0;
    this.filterStateR = 0;
  }

  /**
   * Simple one-pole low-pass filter
   * Simulates the limited frequency response of old DACs
   */
  lowpass(sample, filterState, cutoffFreq, sampleRate) {
    if (!cutoffFreq) return { output: sample, state: filterState };

    const rc = 1.0 / (cutoffFreq * 2 * Math.PI);
    const dt = 1.0 / sampleRate;
    const alpha = dt / (rc + dt);

    const output = filterState + alpha * (sample - filterState);
    return { output, state: output };
  }

  /**
   * Hard clipping to simulate digital distortion
   */
  clip(sample, threshold) {
    if (!this.hardClip) return sample;

    if (sample > threshold) return threshold;
    if (sample < -threshold) return -threshold;
    return sample;
  }

  /**
   * Apply bitcrusher effect to audio buffer
   * @param {Float32Array|Int16Array} inputBuffer - Input audio samples
   * @param {number} sampleRate - Original sample rate
   * @returns {Float32Array} Processed audio samples
   */
  process(inputBuffer, sampleRate) {
    const output = new Float32Array(inputBuffer.length);

    // Convert to float if needed
    let samples;
    if (inputBuffer instanceof Int16Array) {
      samples = new Float32Array(inputBuffer.length);
      for (let i = 0; i < inputBuffer.length; i++) {
        samples[i] = inputBuffer[i] / 32768.0;
      }
    } else {
      samples = new Float32Array(inputBuffer);
    }

    // Calculate quantization steps based on bit depth
    const steps = Math.pow(2, this.bitDepth) - 1;

    let holdSample = 0;
    this.filterStateL = 0; // Reset filter state

    for (let i = 0; i < samples.length; i++) {
      // Sample rate reduction (sample and hold)
      if (i % this.sampleRateReduction === 0) {
        holdSample = samples[i];
      }

      // Bit depth reduction (quantization)
      let processed = Math.round(holdSample * steps) / steps;

      // Hard clipping (simulates digital distortion of old consoles)
      processed = this.clip(processed, this.clipThreshold);

      // Low-pass filter (simulates limited DAC bandwidth)
      if (this.lowpassFreq) {
        const filtered = this.lowpass(processed, this.filterStateL, this.lowpassFreq, sampleRate);
        processed = filtered.output;
        this.filterStateL = filtered.state;
      }

      // Mix wet/dry signal
      output[i] = processed * this.mix + samples[i] * (1 - this.mix);

      // Clamp to valid range
      output[i] = Math.max(-1, Math.min(1, output[i]));
    }

    return output;
  }

  /**
   * Process stereo audio (interleaved left/right channels)
   * @param {Float32Array|Int16Array} inputBuffer - Interleaved stereo samples
   * @param {number} sampleRate - Original sample rate
   * @returns {Float32Array} Processed interleaved stereo samples
   */
  processStereo(inputBuffer, sampleRate) {
    const output = new Float32Array(inputBuffer.length);

    // Convert to float if needed
    let samples;
    if (inputBuffer instanceof Int16Array) {
      samples = new Float32Array(inputBuffer.length);
      for (let i = 0; i < inputBuffer.length; i++) {
        samples[i] = inputBuffer[i] / 32768.0;
      }
    } else {
      samples = new Float32Array(inputBuffer);
    }

    const steps = Math.pow(2, this.bitDepth) - 1;

    let holdSampleL = 0;
    let holdSampleR = 0;
    this.filterStateL = 0; // Reset filter states
    this.filterStateR = 0;

    for (let i = 0; i < samples.length; i += 2) {
      // Sample rate reduction
      if ((i / 2) % this.sampleRateReduction === 0) {
        if (this.monoDownmix) {
          // Mix to mono for authentic old console sound
          const mono = (samples[i] + samples[i + 1]) / 2;
          holdSampleL = mono;
          holdSampleR = mono;
        } else {
          holdSampleL = samples[i];
          holdSampleR = samples[i + 1];
        }
      }

      // Bit depth reduction
      let processedL = Math.round(holdSampleL * steps) / steps;
      let processedR = Math.round(holdSampleR * steps) / steps;

      // Hard clipping
      processedL = this.clip(processedL, this.clipThreshold);
      processedR = this.clip(processedR, this.clipThreshold);

      // Low-pass filter
      if (this.lowpassFreq) {
        const filteredL = this.lowpass(processedL, this.filterStateL, this.lowpassFreq, sampleRate);
        const filteredR = this.lowpass(processedR, this.filterStateR, this.lowpassFreq, sampleRate);
        processedL = filteredL.output;
        processedR = filteredR.output;
        this.filterStateL = filteredL.state;
        this.filterStateR = filteredR.state;
      }

      // Mix wet/dry signal and clamp
      output[i] = Math.max(-1, Math.min(1,
        processedL * this.mix + samples[i] * (1 - this.mix)));
      output[i + 1] = Math.max(-1, Math.min(1,
        processedR * this.mix + samples[i + 1] * (1 - this.mix)));
    }

    return output;
  }
}

/**
 * Preset configurations for different chiptune styles
 */
export const presets = {
  // Classic 8-bit consoles
  gameboy: {
    name: 'Game Boy',
    bitDepth: 4,
    sampleRateReduction: 8,
    mix: 1.0,
    lowpassFreq: 4000,        // Limited speaker bandwidth
    hardClip: true,
    clipThreshold: 0.85,
    monoDownmix: true,        // Game Boy was mono
    description: 'Classic Game Boy lo-fi sound with mono output'
  },
  nes: {
    name: 'Nintendo NES',
    bitDepth: 4,
    sampleRateReduction: 6,
    mix: 1.0,
    lowpassFreq: 8000,        // Triangle/pulse wave harmonics
    hardClip: true,
    clipThreshold: 0.9,
    monoDownmix: true,        // NES was mono
    description: 'Nintendo Entertainment System style (mono)'
  },
  sega: {
    name: 'Sega Genesis/Mega Drive',
    bitDepth: 8,
    sampleRateReduction: 3,
    mix: 1.0,
    lowpassFreq: 12000,       // Better quality DAC
    hardClip: false,          // Cleaner output
    monoDownmix: false,       // Genesis had stereo
    description: 'Sega Genesis FM synthesis style (stereo)'
  },
  snes: {
    name: 'Super Nintendo',
    bitDepth: 8,
    sampleRateReduction: 2,
    mix: 0.9,
    lowpassFreq: 15000,       // High quality samples
    hardClip: false,
    monoDownmix: false,       // SNES had stereo
    description: 'SNES higher quality samples (stereo)'
  },
  // Retro computers
  c64: {
    name: 'Commodore 64',
    bitDepth: 8,
    sampleRateReduction: 4,
    mix: 1.0,
    lowpassFreq: 6000,        // SID chip filtering
    hardClip: true,
    clipThreshold: 0.8,
    monoDownmix: true,        // C64 was mono
    description: 'C64 SID chip sound (mono)'
  },
  atari: {
    name: 'Atari 2600',
    bitDepth: 3,
    sampleRateReduction: 10,
    mix: 1.0,
    lowpassFreq: 3000,        // Very limited
    hardClip: true,
    clipThreshold: 0.75,
    monoDownmix: true,
    description: 'Extremely lo-fi Atari 2600 sound (mono)'
  },
  // Modern interpretations
  mild: {
    name: 'Mild Crunch',
    bitDepth: 12,
    sampleRateReduction: 2,
    mix: 0.7,
    lowpassFreq: null,        // No filtering
    hardClip: false,
    monoDownmix: false,
    description: 'Subtle vintage digital sound'
  },
  heavy: {
    name: 'Heavy Crush',
    bitDepth: 6,
    sampleRateReduction: 8,
    mix: 1.0,
    lowpassFreq: 5000,
    hardClip: true,
    clipThreshold: 0.7,
    monoDownmix: false,
    description: 'Aggressive bitcrushed sound'
  },
  extreme: {
    name: 'Extreme',
    bitDepth: 2,
    sampleRateReduction: 16,
    mix: 1.0,
    lowpassFreq: 2000,
    hardClip: true,
    clipThreshold: 0.6,
    monoDownmix: true,
    description: 'Maximum destruction'
  }
};
