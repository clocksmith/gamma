#!/usr/bin/env node

import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

import {
  deriveWgslTrainingRows,
  readJsonlFile,
  verifyRawWgslRollouts,
  writeDerivedWgslTrainingRows,
  writeVerifiedWgslRollouts,
} from './lib/wgsl-rollout-verifier.js';

function parseArgs(argv) {
  const parsed = { sourceRoots: [] };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    const value = argv[index + 1];
    if (!token.startsWith('--') || !value) throw new Error(`${token} requires a value.`);
    parsed[token.slice(2)] = value;
    index += 1;
  }
  return parsed;
}

async function readPolicy(path) {
  return JSON.parse(await readFile(resolve(path), 'utf8'));
}

export async function main(argv = process.argv.slice(2)) {
  const args = parseArgs(argv);
  const phase = args.phase;
  const policy = await readPolicy(args.policy || 'tools/policies/wgsl-repair-v9-policy.json');
  if (phase === 'verify') {
    const tasks = await readJsonlFile(args.tasks, 'tasks');
    const rawGroups = await readJsonlFile(args.rollouts, 'raw rollouts');
    const verified = await verifyRawWgslRollouts({
      policy,
      tasks,
      rawGroups,
      workloadId: args['workload-id'],
      datasetHash: args['dataset-hash'],
      policyHash: args['policy-hash'],
      referencePolicyHash: args['reference-policy-hash'],
    });
    const outputRoot = await writeVerifiedWgslRollouts(args.output, verified);
    console.log(JSON.stringify({ ok: true, phase, outputRoot, receipt: verified.receipt }, null, 2));
    return;
  }
  if (phase === 'derive') {
    const [groups, tasks] = await Promise.all([
      readJsonlFile(args.groups, 'verified rollout groups'),
      args.tasks ? readJsonlFile(args.tasks, 'WGSL rollout tasks') : null,
    ]);
    const derived = deriveWgslTrainingRows(groups, policy, tasks);
    const outputRoot = await writeDerivedWgslTrainingRows(args.output, derived);
    console.log(JSON.stringify({ ok: true, phase, outputRoot, receipt: derived.receipt }, null, 2));
    return;
  }
  throw new Error('--phase must be verify or derive.');
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(error?.stack || error?.message || String(error));
    process.exitCode = 1;
  });
}
