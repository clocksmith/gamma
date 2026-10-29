#!/usr/bin/env node

import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

import { sha256Hex } from '../src/utils/sha256.js';
import {
  compareVerifiedWgslRollouts,
  exactMcNemarLogPValue,
} from './lib/wgsl-rollout-comparison.js';
import { parseJsonl } from './lib/wgsl-rollout-verifier.js';

const STRATA = Object.freeze(['short', 'long']);

function parseArgs(argv) {
  const args = {};
  for (let index = 0; index < argv.length; index += 2) {
    const token = argv[index];
    const value = argv[index + 1];
    if (!token?.startsWith('--') || !value) throw new Error(`${token} requires a value.`);
    args[token.slice(2)] = value;
  }
  for (const side of ['reference', 'candidate']) {
    for (const stratum of STRATA) {
      const field = `${side}-${stratum}`;
      if (!args[field]) throw new Error(`--${field} is required.`);
    }
  }
  if (!args.output) throw new Error('--output is required.');
  return args;
}

function requireEqual(values, label) {
  if (new Set(values).size !== 1) throw new Error(`${label} differs across strata.`);
  return values[0];
}

function combineSummary(comparisons, side) {
  const summaries = comparisons.map((comparison) => comparison[side]);
  const sum = (field) => summaries.reduce((total, summary) => total + summary[field], 0);
  const taskCount = sum('taskCount');
  const sampleCount = sum('sampleCount');
  const passingSamples = sum('passingSamples');
  const passingTasksAt1 = sum('passingTasksAt1');
  const passingTasksAtK = sum('passingTasksAtK');
  return {
    taskCount,
    groupSize: requireEqual(summaries.map((summary) => summary.groupSize), `${side}.groupSize`),
    sampleCount,
    passingSamples,
    samplePassRate: passingSamples / sampleCount,
    passingTasksAt1,
    passAt1: passingTasksAt1 / taskCount,
    passingTasksAtK,
    passAtK: passingTasksAtK / taskCount,
    exactReferenceSamples: sum('exactReferenceSamples'),
    blockedSamples: sum('blockedSamples'),
  };
}

function combinePaired(comparisons, metric) {
  const rows = comparisons.map((comparison) => comparison.paired[metric]);
  const sum = (field) => rows.reduce((total, row) => total + row[field], 0);
  const referenceOnly = sum('referenceOnly');
  const candidateOnly = sum('candidateOnly');
  const exactMcNemarLogP = exactMcNemarLogPValue(referenceOnly, candidateOnly);
  const exactMcNemarP = Math.exp(exactMcNemarLogP);
  return {
    bothPass: sum('bothPass'),
    bothFail: sum('bothFail'),
    referenceOnly,
    candidateOnly,
    discordant: referenceOnly + candidateOnly,
    exactMcNemarP,
    exactMcNemarLogP,
    exactMcNemarLog10P: exactMcNemarLogP / Math.log(10),
    exactMcNemarPUnderflow: exactMcNemarP === 0 && exactMcNemarLogP < 0,
  };
}

export function combineStratumComparisons(strata) {
  const comparisons = STRATA.map((stratum) => strata[stratum]);
  const referencePolicyHash = requireEqual(
    comparisons.map((comparison) => comparison.referencePolicyHash),
    'referencePolicyHash'
  );
  const candidatePolicyHash = requireEqual(
    comparisons.map((comparison) => comparison.candidatePolicyHash),
    'candidatePolicyHash'
  );
  const anchorPolicyHash = requireEqual(
    comparisons.map((comparison) => comparison.anchorPolicyHash),
    'anchorPolicyHash'
  );
  const verifierBundleHash = requireEqual(
    comparisons.map((comparison) => comparison.verifierBundleHash),
    'verifierBundleHash'
  );
  const runtimeHash = requireEqual(
    comparisons.map((comparison) => comparison.runtimeHash),
    'runtimeHash'
  );
  const reference = combineSummary(comparisons, 'reference');
  const candidate = combineSummary(comparisons, 'candidate');
  return {
    artifactType: 'wgsl_stratified_rollout_comparison',
    schemaVersion: 1,
    stratifiedDatasetHash: sha256Hex(JSON.stringify(STRATA.map((stratum) => ({
      id: stratum,
      datasetHash: strata[stratum].datasetHash,
    })))),
    referencePolicyHash,
    candidatePolicyHash,
    anchorPolicyHash,
    verifierBundleHash,
    runtimeHash,
    samplingByStratum: Object.fromEntries(STRATA.map((stratum) => [
      stratum,
      strata[stratum].sampling,
    ])),
    strata,
    reference,
    candidate,
    effects: {
      samplePassRate: candidate.samplePassRate - reference.samplePassRate,
      passAt1: candidate.passAt1 - reference.passAt1,
      passAtK: candidate.passAtK - reference.passAtK,
    },
    paired: {
      samples: combinePaired(comparisons, 'samples'),
      passAt1: combinePaired(comparisons, 'passAt1'),
      passAtK: combinePaired(comparisons, 'passAtK'),
    },
    claimBoundary: 'Task-weighted short-plus-long compiler-repair comparison; not semantic-kernel or promotion evidence.',
  };
}

async function readGroups(path, label) {
  return parseJsonl(await readFile(resolve(path), 'utf8'), label);
}

export async function main(argv = process.argv.slice(2)) {
  const args = parseArgs(argv);
  const strata = {};
  for (const stratum of STRATA) {
    const [reference, candidate] = await Promise.all([
      readGroups(args[`reference-${stratum}`], `reference ${stratum}`),
      readGroups(args[`candidate-${stratum}`], `candidate ${stratum}`),
    ]);
    strata[stratum] = compareVerifiedWgslRollouts(reference, candidate);
  }
  const comparison = combineStratumComparisons(strata);
  const outputPath = resolve(args.output);
  await mkdir(dirname(outputPath), { recursive: true });
  await writeFile(outputPath, `${JSON.stringify(comparison, null, 2)}\n`, 'utf8');
  console.log(JSON.stringify({ ok: true, outputPath, comparison }, null, 2));
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(error?.stack || error?.message || String(error));
    process.exitCode = 1;
  });
}
