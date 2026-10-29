#!/usr/bin/env node

import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { dirname, join, relative, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

import { sha256BytesHex } from '../src/utils/sha256.js';

const DEFAULT_POLICY = 'tools/policies/wgsl-repair-v12-evaluation-policy.json';

function parseArgs(argv) {
  const args = { policy: DEFAULT_POLICY };
  for (let index = 0; index < argv.length; index += 2) {
    const token = argv[index];
    const value = argv[index + 1];
    if (!token?.startsWith('--') || !value) throw new Error(`${token} requires a value.`);
    args[token.slice(2)] = value;
  }
  if (!args.root || !args.output) throw new Error('--root and --output are required.');
  return args;
}

function requireObject(value, label) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new Error(`${label} must be an object.`);
  }
  return value;
}

function mean(values) {
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function metric(receipt, path) {
  let value = receipt;
  for (const key of path) value = value?.[key];
  if (!Number.isFinite(value)) throw new Error(`Missing metric ${path.join('.')}.`);
  return value;
}

export function decideLaneMatrix(matrix, policy) {
  const seeds = policy.selection.seeds;
  const lanes = policy.selection.lanes;
  for (const seed of seeds) {
    for (const lane of lanes) {
      const receipt = requireObject(matrix?.[seed]?.[lane], `matrix.${seed}.${lane}`);
      if (receipt.seed !== seed || receipt.lane !== lane || receipt.split !== 'diagnostic') {
        throw new Error(`Receipt identity mismatch for seed ${seed} lane ${lane}.`);
      }
    }
  }
  const passAt1 = (seed, lane) => metric(matrix[seed][lane], ['overall', 'passAt1']);
  const longPassAt1 = (seed, lane) => (
    metric(matrix[seed][lane], ['strata', 'long', 'verification', 'passAt1'])
  );
  const treatmentBeatsAnchorEverySeed = seeds.every((seed) => (
    passAt1(seed, 'external20') > passAt1(seed, 'anchor')
  ));
  const treatmentMean = mean(seeds.map((seed) => passAt1(seed, 'external20')));
  const randomMean = mean(seeds.map((seed) => passAt1(seed, 'random20')));
  const anchorMean = mean(seeds.map((seed) => passAt1(seed, 'anchor')));
  const treatmentLongMean = mean(seeds.map((seed) => longPassAt1(seed, 'external20')));
  const anchorLongMean = mean(seeds.map((seed) => longPassAt1(seed, 'anchor')));
  const treatmentBeatsRandomMean = treatmentMean > randomMean;
  const longNonRegression = treatmentLongMean >= anchorLongMean;
  const passed = treatmentBeatsAnchorEverySeed && treatmentBeatsRandomMean && longNonRegression;
  return {
    artifactType: 'wgsl_v12_lane_decision',
    schemaVersion: 1,
    policyId: policy.policyId,
    status: passed ? 'candidate_selected' : 'hypothesis_rejected',
    selectedLane: passed ? 'external20' : null,
    publicEvaluationAllowed: passed,
    checks: {
      treatmentBeatsAnchorEverySeed,
      treatmentBeatsRandomMean,
      longNonRegression,
    },
    aggregate: {
      anchorMeanPassAt1: anchorMean,
      external20MeanPassAt1: treatmentMean,
      random20MeanPassAt1: randomMean,
      anchorMeanLongPassAt1: anchorLongMean,
      external20MeanLongPassAt1: treatmentLongMean,
    },
    perSeed: Object.fromEntries(seeds.map((seed) => [seed, Object.fromEntries(
      lanes.map((lane) => [lane, {
        passAt1: passAt1(seed, lane),
        passAt8: metric(matrix[seed][lane], ['overall', 'passAtK']),
        samplePassRate: metric(matrix[seed][lane], ['overall', 'samplePassRate']),
        shortPassAt1: metric(matrix[seed][lane], ['strata', 'short', 'verification', 'passAt1']),
        longPassAt1: longPassAt1(seed, lane),
        policyHash: matrix[seed][lane].policyHash,
      }])
    )])),
    frozenRule: policy.selection.successRule,
    claimBoundary: passed
      ? 'Diagnostic data-lane candidate selection only; public and semantic evaluation remain absent.'
      : 'The preregistered external20 diagnostic hypothesis failed; public V12 evaluation remains closed.',
  };
}

async function readJson(path) {
  return JSON.parse(await readFile(resolve(path), 'utf8'));
}

async function readMatrix(root, policy) {
  const matrix = {};
  const artifacts = [];
  for (const seed of policy.selection.seeds) {
    matrix[seed] = {};
    for (const lane of policy.selection.lanes) {
      const path = join(root, `seed${seed}`, lane, 'evaluation', 'diagnostic', 'stratified-evaluation.json');
      const bytes = await readFile(path);
      matrix[seed][lane] = JSON.parse(bytes.toString('utf8'));
      artifacts.push({
        seed,
        lane,
        path: relative(process.cwd(), path).replace(/\\/g, '/'),
        sha256: sha256BytesHex(new Uint8Array(bytes)),
      });
    }
  }
  return { matrix, artifacts };
}

export async function main(argv = process.argv.slice(2)) {
  const args = parseArgs(argv);
  const policy = await readJson(args.policy);
  const root = resolve(args.root);
  const { matrix, artifacts } = await readMatrix(root, policy);
  const decision = {
    ...decideLaneMatrix(matrix, policy),
    inputs: artifacts,
  };
  const outputPath = resolve(args.output);
  await mkdir(dirname(outputPath), { recursive: true });
  await writeFile(outputPath, `${JSON.stringify(decision, null, 2)}\n`, 'utf8');
  console.log(JSON.stringify({ ok: true, outputPath, decision }, null, 2));
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(error?.stack || error?.message || String(error));
    process.exitCode = 1;
  });
}
