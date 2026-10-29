#!/usr/bin/env node

import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

import {
  checkWgslWriterV3Corpus,
  materializeWgslWriterV3Corpus,
  writeWgslWriterV3Corpus,
} from './lib/wgsl-writer-v3-corpus.js';

const DEFAULT_POLICY = 'tools/policies/wgsl-writer-v3-corpus-policy.json';
const POLICY_IDS = new Set([
  'doppler-wgsl-writer-v3-corpus',
  'doppler-wgsl-writer-v3-corpus-diversity-repair',
  'doppler-wgsl-writer-v3-explicit-semantic-repair',
  'doppler-wgsl-writer-v3-explicit-output-budget',
]);

function parseArgs(argv) {
  const args = { policyPath: DEFAULT_POLICY, check: false };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === '--policy') args.policyPath = argv[++index] || '';
    else if (token === '--check') args.check = true;
    else throw new Error(`Unknown argument: ${token}`);
  }
  if (!args.policyPath) throw new Error('--policy requires a value.');
  return args;
}

async function readJson(filePath) {
  return JSON.parse(await readFile(filePath, 'utf8'));
}

async function sha256File(filePath) {
  return createHash('sha256').update(await readFile(filePath)).digest('hex');
}

async function requireBinding(binding, label) {
  const actual = await sha256File(binding.path);
  if (actual !== binding.sha256) {
    throw new Error(`${label} SHA-256 mismatch: expected ${binding.sha256}, got ${actual}.`);
  }
}

export async function main(argv = process.argv.slice(2)) {
  const args = parseArgs(argv);
  const repoRoot = resolve(new URL('..', import.meta.url).pathname);
  const policyPath = resolve(repoRoot, args.policyPath);
  const policy = await readJson(policyPath);
  if (!POLICY_IDS.has(policy.policyId)
    || policy.status !== 'frozen_before_materialization') {
    throw new Error('WGSL writer v3 corpus builder requires the frozen materialization policy.');
  }
  await Promise.all([
    requireBinding(policy.predecessor.referenceQualification, 'reference qualification'),
    requireBinding(policy.corpus.capabilityCatalog, 'capability catalog'),
  ]);
  const materialized = materializeWgslWriterV3Corpus({
    repoRoot,
    outputRoot: resolve(repoRoot, policy.corpus.outputRoot),
    catalog: await readJson(resolve(repoRoot, policy.corpus.capabilityCatalog.path)),
    catalogPath: policy.corpus.capabilityCatalog.path,
    catalogSha256: policy.corpus.capabilityCatalog.sha256,
    policy,
    policyPath: args.policyPath,
    policySha256: await sha256File(policyPath),
  });
  const operation = args.check
    ? await checkWgslWriterV3Corpus(materialized)
    : await writeWgslWriterV3Corpus(materialized);
  process.stdout.write(`${JSON.stringify({
    ok: true,
    mode: args.check ? 'check' : 'write',
    outputRoot: policy.corpus.outputRoot,
    rows: Object.fromEntries(Object.entries(materialized.rowsByRole)
      .map(([role, rows]) => [role, rows.length])),
    qualificationTasks: materialized.qualificationManifest.tasks.length,
    manifestSha256: materialized.manifest.manifestSha256,
    operation,
  }, null, 2)}\n`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(error instanceof Error ? error.stack : String(error));
    process.exitCode = 1;
  });
}
