#!/usr/bin/env node

import { program } from 'commander';
import wav from 'node-wav';
import fs from 'fs';
import path from 'path';
import { Bitcrusher, presets } from './bitcrusher.js';

/**
 * Process a WAV file with bitcrusher effect
 */
function processWavFile(inputPath, outputPath, options) {
  console.log(`Reading: ${inputPath}`);

  // Read input WAV file
  const buffer = fs.readFileSync(inputPath);
  const result = wav.decode(buffer);

  console.log(`Sample Rate: ${result.sampleRate} Hz`);
  console.log(`Channels: ${result.channelData.length}`);
  console.log(`Duration: ${(result.channelData[0].length / result.sampleRate).toFixed(2)}s`);

  // Create bitcrusher with specified options
  const bitcrusher = new Bitcrusher({
    bitDepth: options.bitDepth,
    sampleRateReduction: options.sampleRate,
    mix: options.mix
  });

  console.log(`\nApplying bitcrusher effect:`);
  console.log(`  Bit Depth: ${options.bitDepth} bits`);
  console.log(`  Sample Rate Reduction: ${options.sampleRate}x`);
  console.log(`  Mix: ${(options.mix * 100).toFixed(0)}%`);
  if (options.lowpassFreq) {
    console.log(`  Low-pass Filter: ${options.lowpassFreq} Hz`);
  }
  if (options.hardClip) {
    console.log(`  Hard Clipping: enabled (threshold: ${options.clipThreshold})`);
  }
  if (options.monoDownmix) {
    console.log(`  Mono Downmix: enabled`);
  }

  // Process audio
  let processedChannels;

  if (result.channelData.length === 1) {
    // Mono
    const processed = bitcrusher.process(result.channelData[0], result.sampleRate);
    processedChannels = [processed];
  } else if (result.channelData.length === 2) {
    // Stereo - interleave channels
    const interleaved = new Float32Array(result.channelData[0].length * 2);
    for (let i = 0; i < result.channelData[0].length; i++) {
      interleaved[i * 2] = result.channelData[0][i];
      interleaved[i * 2 + 1] = result.channelData[1][i];
    }

    const processed = bitcrusher.processStereo(interleaved, result.sampleRate);

    // De-interleave
    const leftChannel = new Float32Array(result.channelData[0].length);
    const rightChannel = new Float32Array(result.channelData[0].length);
    for (let i = 0; i < result.channelData[0].length; i++) {
      leftChannel[i] = processed[i * 2];
      rightChannel[i] = processed[i * 2 + 1];
    }

    processedChannels = [leftChannel, rightChannel];
  } else {
    console.error('Error: Only mono and stereo files are supported');
    process.exit(1);
  }

  // Encode and write output
  const outputBuffer = wav.encode(processedChannels, {
    sampleRate: result.sampleRate,
    float: false,
    bitDepth: 16
  });

  fs.writeFileSync(outputPath, Buffer.from(outputBuffer));
  console.log(`\nOutput saved to: ${outputPath}`);
}

/**
 * List available presets
 */
function listPresets() {
  console.log('\nAvailable Presets:\n');

  const categories = {
    'Classic Consoles': ['gameboy', 'nes', 'sega', 'snes'],
    'Retro Computers': ['c64', 'atari'],
    'Modern Effects': ['mild', 'heavy', 'extreme']
  };

  for (const [category, presetNames] of Object.entries(categories)) {
    console.log(`${category}:`);
    for (const name of presetNames) {
      const preset = presets[name];
      console.log(`  ${name.padEnd(10)} - ${preset.name}`);
      console.log(`               ${preset.description}`);
      const specs = [`${preset.bitDepth}-bit`, `${preset.sampleRateReduction}x reduction`];
      if (preset.lowpassFreq) specs.push(`${preset.lowpassFreq}Hz LP`);
      if (preset.hardClip) specs.push('clipping');
      if (preset.monoDownmix) specs.push('mono');
      console.log(`               (${specs.join(', ')})\n`);
    }
  }
}

// Setup CLI
program
  .name('bitcrusher')
  .description('Apply bitcrusher effects to WAV files for chiptune-style audio')
  .version('1.0.0');

program
  .command('process')
  .description('Process a WAV file with bitcrusher effect')
  .argument('<input>', 'Input WAV file path')
  .argument('[output]', 'Output WAV file path (default: input_crushed.wav)')
  .option('-p, --preset <name>', 'Use a preset (gameboy, nes, sega, snes, c64, atari, mild, heavy, extreme)')
  .option('-b, --bit-depth <number>', 'Bit depth (1-16)', parseFloat)
  .option('-s, --sample-rate <number>', 'Sample rate reduction factor', parseFloat)
  .option('-m, --mix <number>', 'Wet/dry mix (0.0-1.0)', parseFloat, 1.0)
  .action((input, output, options) => {
    // Determine output path
    if (!output) {
      const parsed = path.parse(input);
      output = path.join(parsed.dir, `${parsed.name}_crushed${parsed.ext}`);
    }

    // Determine effect parameters
    let effectOptions;

    if (options.preset) {
      const presetName = options.preset.toLowerCase();
      if (!presets[presetName]) {
        console.error(`Error: Unknown preset "${options.preset}"`);
        console.log('\nRun "bitcrusher presets" to see available presets');
        process.exit(1);
      }

      effectOptions = { ...presets[presetName] };
      console.log(`Using preset: ${effectOptions.name}`);
    } else {
      effectOptions = {
        bitDepth: options.bitDepth || 8,
        sampleRate: options.sampleRate || 4,
        mix: options.mix
      };
    }

    // Override preset values if custom parameters are provided
    if (options.bitDepth) effectOptions.bitDepth = options.bitDepth;
    if (options.sampleRate) effectOptions.sampleRate = options.sampleRate;
    if (options.mix !== undefined) effectOptions.mix = options.mix;

    // Validate parameters
    if (effectOptions.bitDepth < 1 || effectOptions.bitDepth > 16) {
      console.error('Error: Bit depth must be between 1 and 16');
      process.exit(1);
    }

    if (effectOptions.sampleRate < 1) {
      console.error('Error: Sample rate reduction must be at least 1');
      process.exit(1);
    }

    if (effectOptions.mix < 0 || effectOptions.mix > 1) {
      console.error('Error: Mix must be between 0.0 and 1.0');
      process.exit(1);
    }

    // Check if input file exists
    if (!fs.existsSync(input)) {
      console.error(`Error: Input file not found: ${input}`);
      process.exit(1);
    }

    // Process the file
    try {
      processWavFile(input, output, effectOptions);
    } catch (error) {
      console.error('Error processing file:', error.message);
      process.exit(1);
    }
  });

program
  .command('presets')
  .description('List all available presets')
  .action(() => {
    listPresets();
  });

// Show help if no arguments
if (process.argv.length === 2) {
  program.help();
}

program.parse();
