import { execFile } from 'node:child_process';
import { mkdir, readFile, readdir, writeFile } from 'node:fs/promises';
import { basename, isAbsolute, join, relative, resolve } from 'node:path';
import { promisify } from 'node:util';

import {
  buildWgslRepairTask,
  createWgslRepairMutations,
  deriveKernelFamily,
} from '../../src/experimental/training/wgsl-repair.js';
import { sha256Hex } from '../../src/utils/sha256.js';
import { createWgslBrowserVerifier } from './wgsl-browser-verifier.js';

const execFileAsync = promisify(execFile);

function isObject(value) {
  return value != null && typeof value === 'object' && !Array.isArray(value);
}

function requireString(value, label) {
  const normalized = typeof value === 'string' ? value.trim() : '';
  if (!normalized) throw new Error(`${label} is required.`);
  return normalized;
}

async function walkWgslFiles(root, cursor = root) {
  const entries = await readdir(cursor, { withFileTypes: true });
  const files = [];
  for (const entry of entries.sort((left, right) => left.name.localeCompare(right.name))) {
    if (entry.name === '.git' || entry.name === 'node_modules') continue;
    const path = join(cursor, entry.name);
    if (entry.isDirectory()) {
      files.push(...await walkWgslFiles(root, path));
    } else if (entry.isFile() && entry.name.endsWith('.wgsl')) {
      files.push(path);
    }
  }
  return files;
}

async function readGitRevision(root) {
  const result = await execFileAsync('git', ['-C', root, 'rev-parse', 'HEAD'], {
    encoding: 'utf8',
  });
  return result.stdout.trim();
}

function validateCatalog(catalog) {
  if (!isObject(catalog) || catalog.schemaVersion !== 1 || catalog.source !== 'doppler') {
    throw new Error('WGSL source catalog must be a Doppler schemaVersion=1 object.');
  }
  if (!Array.isArray(catalog.sources) || catalog.sources.length < 1) {
    throw new Error('WGSL source catalog requires sources.');
  }
  const ids = new Set();
  for (const [index, entry] of catalog.sources.entries()) {
    const id = requireString(entry?.id, `sources[${index}].id`);
    if (ids.has(id)) throw new Error(`Duplicate WGSL source id: ${id}`);
    ids.add(id);
    requireString(entry.repository, `sources[${index}].repository`);
    requireString(entry.revision, `sources[${index}].revision`);
    requireString(entry.license, `sources[${index}].license`);
    requireString(entry.parserKind, `sources[${index}].parserKind`);
  }
  return catalog;
}

export async function loadWgslSourceCatalog(catalogPath) {
  const absolutePath = resolve(String(catalogPath));
  const raw = await readFile(absolutePath, 'utf8');
  return {
    absolutePath,
    raw,
    sha256: sha256Hex(raw),
    catalog: validateCatalog(JSON.parse(raw)),
  };
}

function sourceRootForEntry(entry, options) {
  const configured = options.sourceRoots?.[entry.id];
  if (configured) return resolve(configured);
  if (entry.localPath) return resolve(options.repoRoot, entry.localPath);
  return null;
}

function includeFile(entry, root, filePath) {
  const path = relative(root, filePath).replaceAll('\\', '/');
  const includeRoots = Array.isArray(entry.includeRoots) ? entry.includeRoots : [];
  if (includeRoots.length > 0 && !includeRoots.some((prefix) => (
    path === prefix || path.startsWith(`${prefix.replace(/\/$/, '')}/`)
  ))) {
    return false;
  }
  const excludes = Array.isArray(entry.excludePathContains) ? entry.excludePathContains : [];
  return !excludes.some((part) => path.includes(part));
}

export async function collectWgslSourceRecords(catalog, options = {}) {
  const repoRoot = resolve(options.repoRoot || '.');
  const records = [];
  const sourceReceipts = [];
  for (const entry of catalog.sources) {
    if (entry.allowTraining !== true || entry.parserKind !== 'wgsl_files') continue;
    const root = sourceRootForEntry(entry, { ...options, repoRoot });
    if (!root) throw new Error(`WGSL source ${entry.id} requires an explicit source root.`);
    const observedRevision = await readGitRevision(root);
    if (observedRevision !== entry.revision) {
      throw new Error(
        `WGSL source revision mismatch for ${entry.id}: expected ${entry.revision}, got ${observedRevision}`
      );
    }
    const files = (await walkWgslFiles(root)).filter((filePath) => includeFile(entry, root, filePath));
    for (const filePath of files) {
      const source = await readFile(filePath, 'utf8');
      const sourcePath = relative(root, filePath).replaceAll('\\', '/');
      records.push({
        sourceId: entry.id,
        sourcePath,
        revision: observedRevision,
        license: entry.license,
        source,
        sourceSha256: sha256Hex(source),
        kernelFamilyId: deriveKernelFamily(entry.id, sourcePath),
      });
    }
    sourceReceipts.push({
      sourceId: entry.id,
      repository: entry.repository,
      root,
      revision: observedRevision,
      license: entry.license,
      fileCount: files.length,
    });
  }
  return { records, sourceReceipts };
}

function splitForFamily(kernelFamilyId, splitWeights) {
  const value = Number.parseInt(sha256Hex(kernelFamilyId).slice(0, 8), 16) / 0xffffffff;
  let cursor = 0;
  for (const split of splitWeights) {
    cursor += split.weight;
    if (value < cursor) return split.id;
  }
  return splitWeights[splitWeights.length - 1].id;
}

function taskForDataset(task, split, verification) {
  return {
    schemaVersion: task.schemaVersion,
    rowId: task.rowId,
    id: task.id,
    taskId: task.taskId,
    taskContract: task.taskContract,
    split,
    kernelFamilyId: task.kernelFamilyId,
    sourceId: task.sourceId,
    sourcePath: task.sourcePath,
    sourceRevision: task.sourceRevision,
    sourceLicense: task.sourceLicense,
    sourceSha256: task.sourceSha256,
    mutation: task.mutation,
    span: task.span,
    prompt: task.prompt,
    completion: task.completion,
    source: task.source,
    verification,
  };
}

function toJsonl(rows) {
  return `${rows.map((row) => JSON.stringify(row)).join('\n')}\n`;
}

function deterministicOrder(rows, seed, label) {
  return [...rows].sort((left, right) => {
    const leftHash = sha256Hex(`${seed}:${label}:${left.taskId}`);
    const rightHash = sha256Hex(`${seed}:${label}:${right.taskId}`);
    return leftHash.localeCompare(rightHash);
  });
}

function buildControlledTrainingLanes(trainRows, corpusPolicy) {
  const laneRows = Number(corpusPolicy.laneRows);
  const externalFraction = Number(corpusPolicy.fixedExternalTrainingFraction);
  const externalRows = Math.round(laneRows * externalFraction);
  const sharedRows = laneRows - externalRows;
  if (!Number.isInteger(laneRows) || laneRows < 1 || externalRows < 1 || sharedRows < 1) {
    throw new Error('WGSL corpus laneRows and fixedExternalTrainingFraction are invalid.');
  }
  const doppler = deterministicOrder(
    trainRows.filter((row) => row.sourceId === 'doppler'),
    corpusPolicy.laneSeed,
    'doppler'
  );
  const external = deterministicOrder(
    trainRows.filter((row) => row.sourceId !== 'doppler'),
    corpusPolicy.laneSeed,
    'external'
  );
  if (doppler.length < sharedRows + (externalRows * 2)) {
    throw new Error(
      `WGSL corpus needs ${sharedRows + (externalRows * 2)} Doppler rows for controlled lanes; found ${doppler.length}.`
    );
  }
  if (external.length < externalRows) {
    throw new Error(`WGSL corpus needs ${externalRows} external rows; found ${external.length}.`);
  }
  const shared = doppler.slice(0, sharedRows);
  const anchorReplacement = doppler.slice(sharedRows, sharedRows + externalRows);
  const randomReplacement = doppler.slice(
    sharedRows + externalRows,
    sharedRows + (externalRows * 2)
  );
  const externalReplacement = external.slice(0, externalRows);
  const taskLanes = {
    anchor: [...shared, ...anchorReplacement],
    external20: [...shared, ...externalReplacement],
    random20: [...shared, ...randomReplacement],
  };
  const lanes = Object.fromEntries(Object.entries(taskLanes).map(([id, rows]) => [
    id,
    rows.map(({ source, span, ...row }) => ({
      ...row,
      span: {
        broken: span.broken,
        reference: span.reference,
      },
    })),
  ]));
  const laneManifest = Object.fromEntries(Object.entries(lanes).map(([id, rows]) => [id, {
    rowCount: rows.length,
    datasetHash: sha256Hex(JSON.stringify(rows)),
    sourceRows: rows.reduce((counts, row) => {
      counts[row.sourceId] = (counts[row.sourceId] || 0) + 1;
      return counts;
    }, {}),
    taskIds: rows.map((row) => row.taskId),
  }]));
  return { lanes, laneManifest };
}

async function writeCorpusFiles(outputRoot, payload) {
  await mkdir(outputRoot, { recursive: true });
  const writes = [];
  for (const [split, rows] of Object.entries(payload.splits)) {
    writes.push(writeFile(join(outputRoot, `${split}.jsonl`), toJsonl(rows), 'utf8'));
  }
  for (const [lane, rows] of Object.entries(payload.lanes)) {
    writes.push(writeFile(join(outputRoot, `train-${lane}.jsonl`), toJsonl(rows), 'utf8'));
  }
  writes.push(writeFile(
    join(outputRoot, 'verification.jsonl'),
    toJsonl(payload.verificationRows),
    'utf8'
  ));
  writes.push(writeFile(
    join(outputRoot, 'corpus-manifest.json'),
    `${JSON.stringify(payload.manifest, null, 2)}\n`,
    'utf8'
  ));
  await Promise.all(writes);
}

export async function buildVerifiedWgslRepairCorpus(options) {
  const policy = options.policy;
  if (!isObject(policy?.corpus)) throw new Error('WGSL repair policy requires corpus config.');
  const { records, sourceReceipts } = await collectWgslSourceRecords(options.catalog, options);
  const ownsVerifier = !options.verifier;
  const verifier = options.verifier || await createWgslBrowserVerifier(policy.verifier.browser);
  try {
    const cleanResults = await verifier.compile(records.map((record) => ({
      id: `${record.sourceId}:${record.sourcePath}`,
      code: record.source,
    })));
    const cleanById = new Map(cleanResults.map((result) => [result.id, result]));
    const candidates = [];
    for (const record of records) {
      const cleanId = `${record.sourceId}:${record.sourcePath}`;
      const cleanResult = cleanById.get(cleanId);
      if (!cleanResult?.passed) continue;
      for (const mutation of createWgslRepairMutations(
        record.source,
        policy.corpus.mutationOperators
      )) {
        const task = buildWgslRepairTask(record, mutation);
        candidates.push({ task, cleanResult });
      }
    }
    const mutantResults = await verifier.compile(candidates.map(({ task }) => ({
      id: task.taskId,
      code: task.mutatedSource,
    })));
    const mutantById = new Map(mutantResults.map((result) => [result.id, result]));
    const splitWeights = Object.entries(policy.corpus.splits).map(([id, config]) => ({
      id,
      weight: Number(config.weight),
    }));
    const splitWeightTotal = splitWeights.reduce((sum, entry) => sum + entry.weight, 0);
    if (Math.abs(splitWeightTotal - 1) > 1e-9) {
      throw new Error(`WGSL corpus split weights must sum to 1, got ${splitWeightTotal}.`);
    }
    const splits = Object.fromEntries(splitWeights.map((entry) => [entry.id, []]));
    const verificationRows = [];
    const seenFingerprints = new Set();
    for (const { task, cleanResult } of candidates) {
      const mutantResult = mutantById.get(task.taskId);
      const fingerprint = sha256Hex(`${task.sourceSha256}:${task.mutation.mutatedSourceSha256}`);
      const accepted = cleanResult.passed === true
        && mutantResult?.passed === false
        && task.completion === task.span.reference
        && !seenFingerprints.has(fingerprint);
      if (accepted) seenFingerprints.add(fingerprint);
      const verification = {
        schemaVersion: 1,
        taskId: task.taskId,
        fingerprint,
        cleanCompile: cleanResult,
        mutantCompile: mutantResult || null,
        referenceRestoresSource: task.completion === task.span.reference,
        referenceSourceSha256: task.sourceSha256,
        accepted,
      };
      verificationRows.push(verification);
      if (!accepted) continue;
      const split = splitForFamily(task.kernelFamilyId, splitWeights);
      splits[split].push(taskForDataset(task, split, {
        fingerprint,
        verifier: 'chromium_webgpu_compilation_info',
        cleanCompilePassed: true,
        mutantCompileFailed: true,
      }));
    }
    const acceptedRows = Object.values(splits).flat();
    const sourceCounts = Object.fromEntries(sourceReceipts.map((source) => [
      source.sourceId,
      acceptedRows.filter((row) => row.sourceId === source.sourceId).length,
    ]));
    const familySets = Object.fromEntries(Object.entries(splits).map(([split, rows]) => [
      split,
      new Set(rows.map((row) => row.kernelFamilyId)),
    ]));
    const familyOverlap = [];
    const splitIds = Object.keys(familySets);
    for (let left = 0; left < splitIds.length; left += 1) {
      for (let right = left + 1; right < splitIds.length; right += 1) {
        for (const family of familySets[splitIds[left]]) {
          if (familySets[splitIds[right]].has(family)) familyOverlap.push(family);
        }
      }
    }
    if (familyOverlap.length > 0) {
      throw new Error(`WGSL corpus split family leakage: ${familyOverlap.join(', ')}`);
    }
    const distinctKernels = new Set(
      acceptedRows.map((row) => `${row.sourceId}:${row.sourcePath}`)
    ).size;
    const controlledLanes = buildControlledTrainingLanes(splits.train, policy.corpus);
    const manifestCore = {
      artifactType: 'wgsl_repair_corpus_manifest',
      schemaVersion: 1,
      policyId: policy.policyId,
      taskContract: policy.corpus.taskContract,
      catalogSha256: options.catalogSha256,
      deviceInfo: verifier.deviceInfo,
      browserArgs: verifier.browserArgs,
      sourceReceipts,
      discoveredSourceFiles: records.length,
      cleanCompilePasses: candidates.length
        ? new Set(candidates.map(({ task }) => `${task.sourceId}:${task.sourcePath}`)).size
        : 0,
      mutationCandidates: candidates.length,
      acceptedRows: acceptedRows.length,
      distinctKernels,
      rejectedRows: candidates.length - acceptedRows.length,
      splitRows: Object.fromEntries(Object.entries(splits).map(([id, rows]) => [id, rows.length])),
      splitFamilies: Object.fromEntries(Object.entries(familySets).map(([id, set]) => [id, set.size])),
      sourceRows: sourceCounts,
      trainingLanes: controlledLanes.laneManifest,
      familyOverlap,
      claimBoundary: 'Compiler-reproducing replacement tasks only; no student capability claim.',
    };
    const manifest = {
      ...manifestCore,
      corpusHash: sha256Hex(JSON.stringify(acceptedRows)),
      manifestHash: sha256Hex(JSON.stringify(manifestCore)),
    };
    if (acceptedRows.length < policy.corpus.minimumVerifiedRows) {
      throw new Error(
        `WGSL corpus produced ${acceptedRows.length} verified rows; policy requires ${policy.corpus.minimumVerifiedRows}.`
      );
    }
    if (distinctKernels < policy.corpus.minimumDistinctKernels) {
      throw new Error(
        `WGSL corpus produced ${distinctKernels} distinct kernels; policy requires ${policy.corpus.minimumDistinctKernels}.`
      );
    }
    await writeCorpusFiles(resolve(options.outputRoot), {
      splits,
      lanes: controlledLanes.lanes,
      verificationRows,
      manifest,
    });
    return {
      outputRoot: resolve(options.outputRoot),
      splits,
      lanes: controlledLanes.lanes,
      verificationRows,
      manifest,
    };
  } finally {
    if (ownsVerifier) await verifier.close();
  }
}

export function parseSourceRootArgs(values) {
  const roots = {};
  for (const value of values) {
    const separator = value.indexOf('=');
    if (separator < 1) throw new Error(`Invalid --source-root value: ${value}`);
    const id = value.slice(0, separator);
    const root = value.slice(separator + 1);
    if (!root || !isAbsolute(resolve(root))) throw new Error(`Invalid source root for ${id}.`);
    roots[id] = resolve(root);
  }
  return roots;
}

export function defaultCorpusOutputRoot(policyId) {
  return resolve('reports', 'training', 'wgsl-repair', basename(policyId), 'corpus');
}
