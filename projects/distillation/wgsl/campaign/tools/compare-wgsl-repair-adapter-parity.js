#!/usr/bin/env node

import { createHash } from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

import { sha256Hex } from '../src/utils/sha256.js';
import { stableSortObject } from '../src/utils/stable-sort-object.js';

const DEFAULT_POLICY = 'tools/policies/wgsl-repair-v12-adapter-parity-policy.json';

function parseSeedPath(value, label) {
  const separator = value.indexOf('=');
  const seed = Number(value.slice(0, separator));
  const filePath = value.slice(separator + 1);
  if (separator < 1 || !Number.isInteger(seed) || seed < 0 || !filePath) {
    throw new Error(`${label} must be seed=path.`);
  }
  return { seed, path: filePath };
}

function parseArgs(argv) {
  const args = {
    policy: DEFAULT_POLICY,
    reference: '',
    dopplerBase: '',
    dopplerAdapters: [],
    out: '',
  };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === '--policy') args.policy = argv[++index] || '';
    else if (token === '--reference') args.reference = argv[++index] || '';
    else if (token === '--doppler-base') args.dopplerBase = argv[++index] || '';
    else if (token === '--doppler-adapter') {
      args.dopplerAdapters.push(parseSeedPath(argv[++index] || '', token));
    } else if (token === '--out') args.out = argv[++index] || '';
    else throw new Error(`Unknown argument: ${token}`);
  }
  for (const field of ['reference', 'dopplerBase', 'out']) {
    if (!args[field]) throw new Error(`--${field.replace(/[A-Z]/g, (value) => `-${value.toLowerCase()}`)} is required.`);
  }
  if (args.dopplerAdapters.length === 0) throw new Error('--doppler-adapter is required.');
  return args;
}

function stableHash(value) {
  return sha256Hex(JSON.stringify(stableSortObject(value)));
}

async function readJson(filePath) {
  return JSON.parse(await fs.readFile(path.resolve(filePath), 'utf8'));
}

async function fileSha256(filePath) {
  const bytes = await fs.readFile(path.resolve(filePath));
  return createHash('sha256').update(bytes).digest('hex');
}

async function readFloat32(filePath) {
  const bytes = await fs.readFile(path.resolve(filePath));
  if (bytes.byteLength % Float32Array.BYTES_PER_ELEMENT !== 0) {
    throw new Error(`${filePath} is not a complete Float32 capture.`);
  }
  const buffer = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
  return new Float32Array(buffer);
}

function finite(value) {
  return typeof value === 'number' && Number.isFinite(value);
}

export function compareFloatArrays(referenceValues, candidateValues) {
  const reference = Array.from(referenceValues || []);
  const candidate = Array.from(candidateValues || []);
  if (reference.length !== candidate.length || reference.length === 0) {
    return {
      comparable: false,
      elementCount: Math.min(reference.length, candidate.length),
      referenceElementCount: reference.length,
      candidateElementCount: candidate.length,
      finite: false,
      maxAbsError: null,
      meanAbsError: null,
      rootMeanSquareError: null,
      cosineSimilarity: null,
    };
  }
  let maxAbsError = 0;
  let sumAbsError = 0;
  let sumSquaredError = 0;
  let dot = 0;
  let referenceSquared = 0;
  let candidateSquared = 0;
  let allFinite = true;
  for (let index = 0; index < reference.length; index += 1) {
    const expected = reference[index];
    const observed = candidate[index];
    if (!finite(expected) || !finite(observed)) {
      allFinite = false;
      continue;
    }
    const error = Math.abs(observed - expected);
    maxAbsError = Math.max(maxAbsError, error);
    sumAbsError += error;
    sumSquaredError += error * error;
    dot += expected * observed;
    referenceSquared += expected * expected;
    candidateSquared += observed * observed;
  }
  const cosineDenominator = Math.sqrt(referenceSquared * candidateSquared);
  return {
    comparable: true,
    elementCount: reference.length,
    referenceElementCount: reference.length,
    candidateElementCount: candidate.length,
    finite: allFinite,
    maxAbsError,
    meanAbsError: sumAbsError / reference.length,
    rootMeanSquareError: Math.sqrt(sumSquaredError / reference.length),
    cosineSimilarity: cosineDenominator > 0 ? dot / cosineDenominator : null,
  };
}

export function l2Norm(values) {
  let sum = 0;
  for (const value of values || []) sum += value * value;
  return Math.sqrt(sum);
}

export function subtractFloatArrays(leftValues, rightValues) {
  const left = Array.from(leftValues || []);
  const right = Array.from(rightValues || []);
  if (left.length !== right.length) throw new Error('Cannot subtract differently sized arrays.');
  return Float32Array.from(left, (value, index) => value - right[index]);
}

export function exactTokenComparison(referenceValues, candidateValues) {
  const reference = Array.from(referenceValues || []);
  const candidate = Array.from(candidateValues || []);
  let commonPrefixLength = 0;
  while (
    commonPrefixLength < reference.length
    && commonPrefixLength < candidate.length
    && reference[commonPrefixLength] === candidate[commonPrefixLength]
  ) {
    commonPrefixLength += 1;
  }
  return {
    exact: reference.length === candidate.length && commonPrefixLength === reference.length,
    referenceCount: reference.length,
    candidateCount: candidate.length,
    commonPrefixLength,
    firstMismatchIndex: commonPrefixLength < Math.max(reference.length, candidate.length)
      ? commonPrefixLength
      : null,
  };
}

export function topKTokenOverlap(referenceRows, candidateRows, count) {
  const reference = new Set((referenceRows || []).slice(0, count).map((entry) => entry.tokenId));
  const candidate = new Set((candidateRows || []).slice(0, count).map((entry) => entry.tokenId));
  let overlap = 0;
  for (const tokenId of reference) if (candidate.has(tokenId)) overlap += 1;
  return { count, overlap, referenceCount: reference.size, candidateCount: candidate.size };
}

function evaluateBase(policy, reference, doppler, referenceLogits, dopplerLogits) {
  const thresholds = policy.thresholds.base;
  const promptTokens = exactTokenComparison(
    reference.probe.promptTokenIds,
    doppler.promptTokens?.ids
  );
  const logits = compareFloatArrays(referenceLogits, dopplerLogits);
  const topK = topKTokenOverlap(reference.base.topK, doppler.topK, policy.thresholds.topK);
  const firstTokenIdExact = reference.base.selectedTokenId === doppler.selectedToken?.tokenId;
  const completionTokens = exactTokenComparison(
    reference.base.completionTokenIds,
    doppler.generation?.tokenIds
  );
  const completionTextExact = reference.base.completionText === doppler.generation?.output;
  const checks = {
    referenceOk: reference.ok === true,
    dopplerOk: doppler.ok === true,
    referenceModelIdentity:
      reference.model.configSha256 === policy.sourceModel.configSha256
      && reference.model.tokenizerSha256 === policy.sourceModel.tokenizerSha256,
    dopplerModelIdentity:
      doppler.artifactFiles?.['manifest.json']?.sha256
        === policy.dopplerBaseArtifact.manifestSha256
      && doppler.artifactFiles?.['tokenizer.json']?.sha256
        === policy.dopplerBaseArtifact.tokenizerSha256,
    promptIdentity: reference.probe.datasetSha256 === policy.probe.datasetSha256
      && reference.probe.rowId === policy.probe.rowId
      && reference.probe.promptSha256 === policy.probe.promptSha256
      && sha256Hex(String(doppler.prompt || '')) === policy.probe.promptSha256
      && doppler.useChatTemplate === policy.probe.useChatTemplate,
    promptTokenIdsExact: promptTokens.exact,
    firstTokenIdExact,
    logitsFinite: logits.finite,
    logitCosineSimilarity: finite(logits.cosineSimilarity)
      && logits.cosineSimilarity >= thresholds.minimumLogitCosineSimilarity,
    topKTokenOverlap: topK.overlap >= thresholds.minimumTopKTokenOverlap,
  };
  return {
    pass: Object.values(checks).every(Boolean),
    checks,
    promptTokens,
    firstTokenIdExact,
    logits,
    topK,
    completion: {
      tokens: completionTokens,
      textExact: completionTextExact,
      referenceText: reference.base.completionText,
      dopplerText: doppler.generation?.output ?? null,
    },
  };
}

function evaluateAdapter(options) {
  const {
    policy,
    adapterPolicy,
    reference,
    referenceAdapter,
    doppler,
    referenceBaseLogits,
    dopplerBaseLogits,
    referenceAdapterLogits,
    dopplerAdapterLogits,
  } = options;
  const thresholds = policy.thresholds.adapter;
  const promptTokens = exactTokenComparison(
    reference.probe.promptTokenIds,
    doppler.promptTokens?.ids
  );
  const completionTokens = exactTokenComparison(
    referenceAdapter.completionTokenIds,
    doppler.generation?.tokenIds
  );
  const logits = compareFloatArrays(referenceAdapterLogits, dopplerAdapterLogits);
  const topK = topKTokenOverlap(
    referenceAdapter.topK,
    doppler.topK,
    policy.thresholds.topK
  );
  const referenceDelta = subtractFloatArrays(referenceAdapterLogits, referenceBaseLogits);
  const dopplerDelta = subtractFloatArrays(dopplerAdapterLogits, dopplerBaseLogits);
  const delta = compareFloatArrays(referenceDelta, dopplerDelta);
  const referenceDeltaL2Norm = l2Norm(referenceDelta);
  const dopplerDeltaL2Norm = l2Norm(dopplerDelta);
  const firstTokenIdExact = referenceAdapter.selectedTokenId === doppler.selectedToken?.tokenId;
  const completionTextExact = referenceAdapter.completionText === doppler.generation?.output;
  const checks = {
    dopplerOk: doppler.ok === true,
    promptIdentity: sha256Hex(String(doppler.prompt || '')) === policy.probe.promptSha256
      && doppler.useChatTemplate === policy.probe.useChatTemplate,
    referenceWeightsIdentity:
      referenceAdapter.adapterWeightsSha256 === adapterPolicy.peftWeightsSha256,
    dopplerManifestIdentity:
      doppler.adapter?.artifact?.manifestSha256 === adapterPolicy.dopplerManifestSha256,
    dopplerWeightsIdentity:
      doppler.adapter?.artifact?.weightsSha256 === adapterPolicy.dopplerWeightsSha256,
    adapterActivated: doppler.adapter?.activation?.activated === true,
    promptTokenIdsExact: promptTokens.exact,
    firstTokenIdExact,
    completionTokenIdsExact: completionTokens.exact,
    completionTextExact,
    logitsFinite: logits.finite,
    logitCosineSimilarity: finite(logits.cosineSimilarity)
      && logits.cosineSimilarity >= thresholds.minimumLogitCosineSimilarity,
    topKTokenOverlap: topK.overlap >= thresholds.minimumTopKTokenOverlap,
    adapterDeltaFinite: delta.finite,
    adapterDeltaCosineSimilarity: finite(delta.cosineSimilarity)
      && delta.cosineSimilarity >= thresholds.minimumAdapterDeltaCosineSimilarity,
    referenceAdapterDeltaNonzero:
      referenceDeltaL2Norm >= thresholds.minimumNonzeroAdapterDeltaL2Norm,
    dopplerAdapterDeltaNonzero:
      dopplerDeltaL2Norm >= thresholds.minimumNonzeroAdapterDeltaL2Norm,
  };
  return {
    seed: adapterPolicy.seed,
    pass: Object.values(checks).every(Boolean),
    checks,
    promptTokens,
    firstTokenIdExact,
    completion: {
      tokens: completionTokens,
      textExact: completionTextExact,
      referenceText: referenceAdapter.completionText,
      dopplerText: doppler.generation?.output ?? null,
    },
    logits,
    topK,
    adapterDelta: {
      ...delta,
      referenceL2Norm: referenceDeltaL2Norm,
      dopplerL2Norm: dopplerDeltaL2Norm,
    },
  };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const [policy, reference, dopplerBase] = await Promise.all([
    readJson(args.policy),
    readJson(args.reference),
    readJson(args.dopplerBase),
  ]);
  const dopplerAdapterMap = new Map();
  for (const entry of args.dopplerAdapters) {
    if (dopplerAdapterMap.has(entry.seed)) throw new Error(`Duplicate Doppler seed ${entry.seed}.`);
    dopplerAdapterMap.set(entry.seed, await readJson(entry.path));
  }
  const referenceAdapterMap = new Map(reference.adapters.map((entry) => [entry.seed, entry]));
  const referenceBaseLogits = await readFloat32(reference.base.logits.path);
  const dopplerBaseLogits = await readFloat32(dopplerBase.logitsCapture.path);
  const base = evaluateBase(
    policy,
    reference,
    dopplerBase,
    referenceBaseLogits,
    dopplerBaseLogits
  );
  const adapters = [];
  for (const adapterPolicy of policy.adapters) {
    const referenceAdapter = referenceAdapterMap.get(adapterPolicy.seed);
    const doppler = dopplerAdapterMap.get(adapterPolicy.seed);
    if (!referenceAdapter || !doppler) {
      throw new Error(`Missing parity evidence for seed ${adapterPolicy.seed}.`);
    }
    adapters.push(evaluateAdapter({
      policy,
      adapterPolicy,
      reference,
      referenceAdapter,
      doppler,
      referenceBaseLogits,
      dopplerBaseLogits,
      referenceAdapterLogits: await readFloat32(referenceAdapter.logits.path),
      dopplerAdapterLogits: await readFloat32(doppler.logitsCapture.path),
    }));
  }
  const identities = {
    policy: { path: args.policy, sha256: await fileSha256(args.policy) },
    reference: { path: args.reference, sha256: await fileSha256(args.reference) },
    dopplerBase: { path: args.dopplerBase, sha256: await fileSha256(args.dopplerBase) },
    dopplerAdapters: await Promise.all(args.dopplerAdapters.map(async (entry) => ({
      seed: entry.seed,
      path: entry.path,
      sha256: await fileSha256(entry.path),
    }))),
  };
  const core = {
    schema: 'doppler.wgsl-repair-adapter-parity-receipt/v1',
    policyId: policy.policyId,
    purpose: policy.purpose,
    identities,
    base,
    adapters,
    decision: base.pass && adapters.every((entry) => entry.pass)
      ? 'diagnostic_import_parity_passed'
      : 'diagnostic_import_parity_failed',
    seedSelected: false,
    selectedSeed: null,
    claimBoundary: policy.claimBoundary,
  };
  const receipt = { ...core, receiptHash: stableHash(core) };
  await fs.mkdir(path.dirname(path.resolve(args.out)), { recursive: true });
  await fs.writeFile(path.resolve(args.out), `${JSON.stringify(receipt, null, 2)}\n`, 'utf8');
  process.stdout.write(`${JSON.stringify(receipt, null, 2)}\n`);
  if (receipt.decision !== 'diagnostic_import_parity_passed') process.exitCode = 1;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(error instanceof Error ? error.stack : String(error));
    process.exitCode = 1;
  });
}
