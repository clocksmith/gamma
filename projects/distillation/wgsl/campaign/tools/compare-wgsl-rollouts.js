#!/usr/bin/env node

import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

import { compareVerifiedWgslRollouts } from './lib/wgsl-rollout-comparison.js';
import { parseJsonl } from './lib/wgsl-rollout-verifier.js';

function parseArgs(argv) {
  const args = { reference: null, candidate: null, output: null };
  for (let index = 0; index < argv.length; index += 2) {
    const token = argv[index];
    const value = argv[index + 1];
    if (!value) throw new Error(`${token} requires a value.`);
    if (token === '--reference') args.reference = value;
    else if (token === '--candidate') args.candidate = value;
    else if (token === '--output') args.output = value;
    else throw new Error(`Unknown argument: ${token}`);
  }
  if (!args.reference || !args.candidate || !args.output) {
    throw new Error('--reference, --candidate, and --output are required.');
  }
  return args;
}

export async function main(argv = process.argv.slice(2)) {
  const args = parseArgs(argv);
  const [referenceText, candidateText] = await Promise.all([
    readFile(resolve(args.reference), 'utf8'),
    readFile(resolve(args.candidate), 'utf8'),
  ]);
  const comparison = compareVerifiedWgslRollouts(
    parseJsonl(referenceText, 'reference rollout groups'),
    parseJsonl(candidateText, 'candidate rollout groups')
  );
  const outputPath = resolve(args.output);
  await mkdir(dirname(outputPath), { recursive: true });
  await writeFile(outputPath, `${JSON.stringify(comparison, null, 2)}\n`, 'utf8');
  console.log(JSON.stringify({ ok: true, outputPath, comparison }, null, 2));
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(error?.stack || error);
    process.exitCode = 1;
  });
}
