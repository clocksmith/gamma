#!/usr/bin/env node

import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

import { sha256BytesHex } from '../src/utils/sha256.js';

function parseArgs(argv) {
  const parsed = {
    input: null,
    outputRoot: null,
    thresholdChars: null,
    shortMaxTokens: null,
    longMaxTokens: null,
    derivationSource: null,
    derivationSourceSha256: null,
  };
  for (let index = 0; index < argv.length; index += 2) {
    const token = argv[index];
    const value = argv[index + 1];
    if (!value) throw new Error(`${token} requires a value.`);
    if (token === '--input') parsed.input = value;
    else if (token === '--output-root') parsed.outputRoot = value;
    else if (token === '--threshold-chars') parsed.thresholdChars = Number(value);
    else if (token === '--short-max-tokens') parsed.shortMaxTokens = Number(value);
    else if (token === '--long-max-tokens') parsed.longMaxTokens = Number(value);
    else if (token === '--derivation-source') parsed.derivationSource = value;
    else if (token === '--derivation-source-sha256') parsed.derivationSourceSha256 = value;
    else throw new Error(`Unknown argument: ${token}`);
  }
  if (!parsed.input || !parsed.outputRoot || !parsed.derivationSource) {
    throw new Error('--input, --output-root, and --derivation-source are required.');
  }
  for (const field of ['thresholdChars', 'shortMaxTokens', 'longMaxTokens']) {
    if (!Number.isInteger(parsed[field]) || parsed[field] < 1) {
      throw new Error(`${field} must be a positive integer.`);
    }
  }
  if (parsed.longMaxTokens <= parsed.shortMaxTokens) {
    throw new Error('longMaxTokens must be greater than shortMaxTokens.');
  }
  if (!/^[a-f0-9]{64}$/.test(parsed.derivationSourceSha256 || '')) {
    throw new Error('derivationSourceSha256 must be a SHA-256 digest.');
  }
  return parsed;
}

function parseJsonl(text, label) {
  const rows = text.split('\n').filter((line) => line.trim()).map((line, index) => {
    try {
      return JSON.parse(line);
    } catch (cause) {
      throw new Error(`${label}:${index + 1} is invalid JSON: ${cause.message}`);
    }
  });
  if (rows.length === 0) throw new Error(`${label} contains no rows.`);
  return rows;
}

function toJsonl(rows) {
  return `${rows.map((row) => JSON.stringify(row)).join('\n')}\n`;
}

export function verifyDeclaredSha256(bytes, expected, label) {
  const actual = sha256BytesHex(bytes);
  if (actual !== expected) {
    throw new Error(`${label} SHA-256 mismatch: expected ${expected}, got ${actual}.`);
  }
  return actual;
}

export function partitionWgslTasksByBrokenSpanLength(tasks, thresholdChars) {
  if (!Array.isArray(tasks) || tasks.length === 0) {
    throw new Error('tasks must contain at least one row.');
  }
  if (!Number.isInteger(thresholdChars) || thresholdChars < 1) {
    throw new Error('thresholdChars must be a positive integer.');
  }
  const short = [];
  const long = [];
  for (const [index, task] of tasks.entries()) {
    const broken = task?.span?.broken;
    if (typeof broken !== 'string' || broken.length === 0) {
      throw new Error(`tasks[${index}].span.broken is required.`);
    }
    (broken.length > thresholdChars ? long : short).push(task);
  }
  if (short.length === 0 || long.length === 0) {
    throw new Error('length stratification must produce non-empty short and long partitions.');
  }
  return { short, long };
}

export async function main(argv = process.argv.slice(2)) {
  const args = parseArgs(argv);
  const inputPath = resolve(args.input);
  const inputBytes = new Uint8Array(await readFile(inputPath));
  const derivationSourcePath = resolve(args.derivationSource);
  const derivationSourceBytes = new Uint8Array(await readFile(derivationSourcePath));
  verifyDeclaredSha256(
    derivationSourceBytes,
    args.derivationSourceSha256,
    'derivation source'
  );
  const tasks = parseJsonl(new TextDecoder().decode(inputBytes), inputPath);
  const partitions = partitionWgslTasksByBrokenSpanLength(tasks, args.thresholdChars);
  const shortText = toJsonl(partitions.short);
  const longText = toJsonl(partitions.long);
  const outputRoot = resolve(args.outputRoot);
  const shortPath = resolve(outputRoot, 'short.jsonl');
  const longPath = resolve(outputRoot, 'long.jsonl');
  const manifestPath = resolve(outputRoot, 'length-strata-manifest.json');
  const encoder = new TextEncoder();
  const manifest = {
    artifactType: 'wgsl_length_strata_manifest',
    schemaVersion: 1,
    input: {
      path: args.input,
      rows: tasks.length,
      sha256: sha256BytesHex(inputBytes),
    },
    rule: {
      field: 'span.broken.length',
      unit: 'unicode_code_units',
      thresholdChars: args.thresholdChars,
      shortPredicate: `span.broken.length <= ${args.thresholdChars}`,
      longPredicate: `span.broken.length > ${args.thresholdChars}`,
      shortMaxTokens: args.shortMaxTokens,
      longMaxTokens: args.longMaxTokens,
      holdoutReferenceUsedForAssignment: false,
      derivationSource: args.derivationSource,
      derivationSourceSha256: args.derivationSourceSha256,
    },
    outputs: {
      short: {
        path: shortPath,
        rows: partitions.short.length,
        sha256: sha256BytesHex(encoder.encode(shortText)),
      },
      long: {
        path: longPath,
        rows: partitions.long.length,
        sha256: sha256BytesHex(encoder.encode(longText)),
      },
    },
    claimBoundary: 'Input-visible length stratification only; no model outcome or promotion claim.',
  };
  await mkdir(outputRoot, { recursive: true });
  await Promise.all([
    writeFile(shortPath, shortText, 'utf8'),
    writeFile(longPath, longText, 'utf8'),
    writeFile(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`, 'utf8'),
  ]);
  console.log(JSON.stringify({ ok: true, manifestPath, manifest }, null, 2));
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(error?.stack || error);
    process.exitCode = 1;
  });
}
