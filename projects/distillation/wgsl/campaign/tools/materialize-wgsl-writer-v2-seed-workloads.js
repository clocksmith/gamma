#!/usr/bin/env node

import { readFile, writeFile } from 'node:fs/promises';
import { basename, dirname, join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const WORKLOAD_ROOT = 'src/experimental/training/workload-capsules';
const TEMPLATE_SEED = 11;
const REPLICATION_SEEDS = Object.freeze([29, 47]);

function parseArgs(argv) {
  if (argv.length === 0 || (argv.length === 1 && argv[0] === '--check')) {
    return { write: false };
  }
  if (argv.length === 1 && argv[0] === '--write') return { write: true };
  throw new Error('Usage: materialize-wgsl-writer-v2-seed-workloads.js [--check|--write]');
}

function canonicalJson(value) {
  return `${JSON.stringify(value, null, 2)}\n`;
}

function filename(seed) {
  return `lora-doppler-wgsl-writer-qwen35-9b-v2-seed${seed}.json`;
}

export function buildWriterSeedWorkload(templateValue, seed) {
  if (!templateValue || typeof templateValue !== 'object' || Array.isArray(templateValue)) {
    throw new Error('Writer v2 template workload must be an object.');
  }
  if (!REPLICATION_SEEDS.includes(seed)) {
    throw new Error(`Unsupported writer v2 replication seed: ${seed}`);
  }
  const expectedId = `lora-doppler-wgsl-writer-qwen35-9b-v2-seed${TEMPLATE_SEED}`;
  if (templateValue.id !== expectedId || templateValue.seed !== TEMPLATE_SEED) {
    throw new Error('Writer v2 template must be the frozen seed-11 workload.');
  }
  const workload = structuredClone(templateValue);
  workload.id = `lora-doppler-wgsl-writer-qwen35-9b-v2-seed${seed}`;
  workload.description = templateValue.description.replace('seed 11', `seed ${seed}`);
  workload.claimBoundary = `${templateValue.claimBoundary} This workload is replication seed ${seed}.`;
  workload.seed = seed;
  workload.lora.export.id = `doppler-wgsl-writer-qwen35-9b-v2-seed${seed}`;
  workload.lora.export.name = `Doppler WGSL Writer Qwen 3.5 9B V2 Seed ${seed}`;
  return workload;
}

async function materialize(root, write) {
  const template = JSON.parse(await readFile(join(root, filename(TEMPLATE_SEED)), 'utf8'));
  const outputs = [];
  for (const seed of REPLICATION_SEEDS) {
    const outputPath = join(root, filename(seed));
    const expected = canonicalJson(buildWriterSeedWorkload(template, seed));
    if (write) {
      await writeFile(outputPath, expected, 'utf8');
    } else {
      let actual;
      try {
        actual = await readFile(outputPath, 'utf8');
      } catch {
        throw new Error(`${basename(outputPath)} is missing; run --write.`);
      }
      if (actual !== expected) {
        throw new Error(`${basename(outputPath)} is stale; run --write.`);
      }
    }
    outputs.push({ seed, path: outputPath });
  }
  return outputs;
}

export async function main(argv = process.argv.slice(2)) {
  const args = parseArgs(argv);
  const root = resolve(WORKLOAD_ROOT);
  const outputs = await materialize(root, args.write);
  console.log(JSON.stringify({
    ok: true,
    mode: args.write ? 'write' : 'check',
    root: dirname(outputs[0].path),
    workloads: outputs,
  }, null, 2));
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(error instanceof Error ? error.stack : String(error));
    process.exitCode = 1;
  });
}
