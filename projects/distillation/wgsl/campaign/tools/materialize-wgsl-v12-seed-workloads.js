#!/usr/bin/env node

import { readFile, writeFile } from 'node:fs/promises';
import { basename, dirname, join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const WORKLOAD_ROOT = 'src/experimental/training/workload-capsules';
const LANES = Object.freeze(['anchor', 'external20', 'random20']);
const REPLICATION_SEEDS = Object.freeze([29, 47]);

function parseArgs(argv) {
  if (argv.length === 0 || (argv.length === 1 && argv[0] === '--check')) {
    return { write: false };
  }
  if (argv.length === 1 && argv[0] === '--write') return { write: true };
  throw new Error('Usage: materialize-wgsl-v12-seed-workloads.js [--check|--write]');
}

function canonicalJson(value) {
  return `${JSON.stringify(value, null, 2)}\n`;
}

function requireObject(value, label) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new Error(`${label} must be an object.`);
  }
  return value;
}

export function buildSeedWorkload(templateValue, lane, seed) {
  const template = requireObject(templateValue, 'template workload');
  if (!LANES.includes(lane)) throw new Error(`Unknown V12 lane: ${lane}`);
  if (!REPLICATION_SEEDS.includes(seed)) {
    throw new Error(`Unsupported V12 replication seed: ${seed}`);
  }
  const expectedId = `lora-doppler-wgsl-qwen35-9b-v12-${lane}`;
  if (template.id !== expectedId || template.seed !== 11) {
    throw new Error(`${lane} template must be the frozen seed-11 workload.`);
  }
  const workload = JSON.parse(JSON.stringify(template));
  const id = `${expectedId}-seed${seed}`;
  workload.id = id;
  workload.description = `${template.description}; replication seed ${seed}`;
  workload.claimBoundary = `${template.claimBoundary} This workload is replication seed ${seed}.`;
  workload.seed = seed;
  requireObject(workload.lora, 'workload.lora');
  requireObject(workload.lora.export, 'workload.lora.export');
  workload.lora.export.id = id.replace(/^lora-/, '');
  workload.lora.export.name = `${template.lora.export.name} Seed ${seed}`;
  return workload;
}

function workloadFilename(lane, seed = null) {
  const suffix = seed == null ? '' : `-seed${seed}`;
  return `lora-doppler-wgsl-qwen35-9b-v12-${lane}${suffix}.json`;
}

async function readJson(path) {
  return JSON.parse(await readFile(path, 'utf8'));
}

async function materialize(root, write) {
  const outputs = [];
  for (const lane of LANES) {
    const templatePath = join(root, workloadFilename(lane));
    const template = await readJson(templatePath);
    for (const seed of REPLICATION_SEEDS) {
      const outputPath = join(root, workloadFilename(lane, seed));
      const expected = canonicalJson(buildSeedWorkload(template, lane, seed));
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
      outputs.push({ lane, seed, path: outputPath });
    }
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
    console.error(error?.stack || error?.message || String(error));
    process.exitCode = 1;
  });
}
