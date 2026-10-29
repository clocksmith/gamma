#!/usr/bin/env node

import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

import { runWgslRepairSemanticHarness } from './run-wgsl-repair-semantic-harness.js';

function parseArgs(argv) {
  const args = {
    policyPath: 'tools/policies/wgsl-repair-v13-semantic-policy.json',
    taskManifestPath: '',
    historicalManifestPath: 'tools/data/wgsl-repair-v13-historical-regressions.json',
    mode: 'reference',
    completionsPath: '',
    outputPath: '',
  };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === '--policy') args.policyPath = argv[++index] || '';
    else if (token === '--task-manifest') args.taskManifestPath = argv[++index] || '';
    else if (token === '--historical-regressions') {
      args.historicalManifestPath = argv[++index] || '';
    } else if (token === '--mode') args.mode = argv[++index] || '';
    else if (token === '--completions') args.completionsPath = argv[++index] || '';
    else if (token === '--out') args.outputPath = argv[++index] || '';
    else throw new Error(`Unknown argument: ${token}`);
  }
  if (!args.taskManifestPath) throw new Error('--task-manifest is required.');
  if (!args.outputPath) throw new Error('--out is required.');
  if (!['reference', 'candidate'].includes(args.mode)) {
    throw new Error('--mode must be reference or candidate.');
  }
  if (args.mode === 'candidate' && !args.completionsPath) {
    throw new Error('--completions is required in candidate mode.');
  }
  return args;
}

export async function writeWgslRepairSemanticReceipt(args) {
  const receipt = await runWgslRepairSemanticHarness(args);
  const outputPath = path.resolve(args.outputPath);
  await fs.mkdir(path.dirname(outputPath), { recursive: true });
  await fs.writeFile(outputPath, `${JSON.stringify(receipt, null, 2)}\n`, 'utf8');
  return receipt;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const receipt = await writeWgslRepairSemanticReceipt(args);
  console.error(`[wgsl-semantic-receipt] wrote ${args.outputPath}`);
  if (!receipt.decision.endsWith('_passed')) process.exitCode = 1;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(error instanceof Error ? error.stack : String(error));
    process.exitCode = 1;
  });
}
