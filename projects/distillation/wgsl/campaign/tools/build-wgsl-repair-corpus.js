#!/usr/bin/env node

import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

import {
  buildVerifiedWgslRepairCorpus,
  defaultCorpusOutputRoot,
  loadWgslSourceCatalog,
  parseSourceRootArgs,
} from './lib/wgsl-repair-corpus.js';

function parseArgs(argv) {
  const options = {
    policy: 'tools/policies/wgsl-repair-v9-policy.json',
    catalog: 'tools/data/wgsl-training-source-catalog-v1.json',
    output: null,
    sourceRoots: [],
  };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    const value = argv[index + 1];
    if (token === '--policy' || token === '--catalog' || token === '--output' || token === '--source-root') {
      if (!value) throw new Error(`${token} requires a value.`);
      if (token === '--policy') options.policy = value;
      if (token === '--catalog') options.catalog = value;
      if (token === '--output') options.output = value;
      if (token === '--source-root') options.sourceRoots.push(value);
      index += 1;
      continue;
    }
    throw new Error(`Unknown argument: ${token}`);
  }
  return options;
}

export async function main(argv = process.argv.slice(2)) {
  const args = parseArgs(argv);
  const repoRoot = resolve(new URL('..', import.meta.url).pathname);
  const policyPath = resolve(repoRoot, args.policy);
  const policy = JSON.parse(await readFile(policyPath, 'utf8'));
  const catalogLoaded = await loadWgslSourceCatalog(resolve(repoRoot, args.catalog));
  const outputRoot = args.output
    ? resolve(args.output)
    : defaultCorpusOutputRoot(policy.policyId);
  const result = await buildVerifiedWgslRepairCorpus({
    repoRoot,
    policy,
    catalog: catalogLoaded.catalog,
    catalogSha256: catalogLoaded.sha256,
    sourceRoots: parseSourceRootArgs(args.sourceRoots),
    outputRoot,
  });
  console.log(JSON.stringify({
    ok: true,
    outputRoot: result.outputRoot,
    manifest: {
      policyId: result.manifest.policyId,
      catalogSha256: result.manifest.catalogSha256,
      corpusHash: result.manifest.corpusHash,
      manifestHash: result.manifest.manifestHash,
      deviceInfo: result.manifest.deviceInfo,
      discoveredSourceFiles: result.manifest.discoveredSourceFiles,
      cleanCompilePasses: result.manifest.cleanCompilePasses,
      mutationCandidates: result.manifest.mutationCandidates,
      acceptedRows: result.manifest.acceptedRows,
      distinctKernels: result.manifest.distinctKernels,
      rejectedRows: result.manifest.rejectedRows,
      splitRows: result.manifest.splitRows,
      splitFamilies: result.manifest.splitFamilies,
      sourceRows: result.manifest.sourceRows,
      trainingLanes: Object.fromEntries(Object.entries(result.manifest.trainingLanes).map(
        ([id, lane]) => [id, {
          rowCount: lane.rowCount,
          datasetHash: lane.datasetHash,
          sourceRows: lane.sourceRows,
        }]
      )),
      familyOverlap: result.manifest.familyOverlap,
      claimBoundary: result.manifest.claimBoundary,
    },
  }, null, 2));
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(error?.stack || error?.message || String(error));
    process.exitCode = 1;
  });
}
