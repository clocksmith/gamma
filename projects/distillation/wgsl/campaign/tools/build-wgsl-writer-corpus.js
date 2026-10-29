#!/usr/bin/env node

import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

import {
  checkWgslWriterCorpus,
  materializeWgslWriterCorpus,
  writeWgslWriterCorpus,
} from './lib/wgsl-writer-corpus.js';

const DEFAULT_POLICY = 'tools/policies/wgsl-writer-v2-corpus-policy.json';

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

export async function main(argv = process.argv.slice(2)) {
  const args = parseArgs(argv);
  const repoRoot = resolve(new URL('..', import.meta.url).pathname);
  const policyPath = resolve(repoRoot, args.policyPath);
  const policy = await readJson(policyPath);
  const catalogPath = resolve(repoRoot, policy.corpus.blueprintCatalog.path);
  const catalogSha256 = await sha256File(catalogPath);
  if (catalogSha256 !== policy.corpus.blueprintCatalog.sha256) {
    throw new Error(
      `WGSL writer blueprint catalog SHA-256 mismatch: expected ${policy.corpus.blueprintCatalog.sha256}, got ${catalogSha256}.`
    );
  }
  const materialized = materializeWgslWriterCorpus({
    repoRoot,
    outputRoot: resolve(repoRoot, policy.corpus.outputRoot),
    catalog: await readJson(catalogPath),
    policy,
    policyPath: args.policyPath,
    policySha256: await sha256File(policyPath),
  });
  const operation = args.check
    ? await checkWgslWriterCorpus(materialized)
    : await writeWgslWriterCorpus(materialized);
  process.stdout.write(`${JSON.stringify({
    ok: true,
    mode: args.check ? 'check' : 'write',
    outputRoot: policy.corpus.outputRoot,
    rows: Object.fromEntries(Object.entries(materialized.rowsByRole).map(
      ([role, rows]) => [role, rows.length]
    )),
    semanticFamilies: Object.fromEntries(Object.entries(materialized.manifest.roles).map(
      ([role, value]) => [role, value.semanticFamilyCount]
    )),
    manifestSha256: materialized.manifest.manifestSha256,
    checkedFiles: operation?.checkedFiles || null,
  }, null, 2)}\n`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(error instanceof Error ? error.stack : String(error));
    process.exitCode = 1;
  });
}
