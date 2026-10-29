#!/usr/bin/env node

import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const DEFAULT_POLICY = 'tools/policies/wgsl-repair-v13-confirmation-materialization-policy.json';
const COMMIT_PATTERN = /^[0-9a-f]{40}$/;

function sha256(value) {
  return createHash('sha256').update(value).digest('hex');
}

function parseArgs(argv) {
  const args = { policyPath: DEFAULT_POLICY, freezeCommit: '' };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === '--policy') args.policyPath = argv[++index] || '';
    else if (token === '--freeze-commit') args.freezeCommit = argv[++index] || '';
    else throw new Error(`Unknown argument: ${token}`);
  }
  if (!COMMIT_PATTERN.test(args.freezeCommit)) {
    throw new Error('--freeze-commit must be a full lowercase 40-character Git commit.');
  }
  return args;
}

async function readJson(filePath) {
  return JSON.parse(await fs.readFile(path.resolve(filePath), 'utf8'));
}

async function sha256File(filePath) {
  return sha256(await fs.readFile(path.resolve(filePath)));
}

function gitOutput(args, options = {}) {
  return execFileSync('git', args, {
    cwd: process.cwd(),
    encoding: options.encoding,
    stdio: options.stdio || ['ignore', 'pipe', 'pipe'],
  });
}

function requireFreezeCommit(commit) {
  const resolved = gitOutput(['rev-parse', '--verify', `${commit}^{commit}`], {
    encoding: 'utf8',
  }).trim();
  if (resolved !== commit) {
    throw new Error(`Freeze commit did not resolve exactly: ${commit}.`);
  }
  try {
    gitOutput(['merge-base', '--is-ancestor', commit, 'HEAD']);
  } catch {
    throw new Error(`Freeze commit is not an ancestor of HEAD: ${commit}.`);
  }
}

async function verifyCommitBoundFile(commit, filePath, expectedSha256, label) {
  const currentSha256 = await sha256File(filePath);
  if (currentSha256 !== expectedSha256) {
    throw new Error(`${label} current SHA-256 mismatch.`);
  }
  let committedBytes;
  try {
    committedBytes = gitOutput(['show', `${commit}:${filePath}`]);
  } catch {
    throw new Error(`${label} is absent from freeze commit ${commit}.`);
  }
  const committedSha256 = sha256(committedBytes);
  if (committedSha256 !== expectedSha256) {
    throw new Error(`${label} freeze-commit SHA-256 mismatch.`);
  }
}

function requireBlueprintCatalog(catalog) {
  if (catalog?.schema !== 'doppler.wgsl-repair-v13-confirmation-blueprints/v1'
    || !Array.isArray(catalog.blueprints)
    || catalog.blueprints.length < 2) {
    throw new Error('WGSL V13 confirmation blueprint catalog is invalid.');
  }
  const uniqueFields = ['id', 'oracleId'];
  for (const field of uniqueFields) {
    const values = catalog.blueprints.map((entry) => entry?.[field]);
    if (values.some((value) => typeof value !== 'string' || value.length === 0)
      || new Set(values).size !== values.length) {
      throw new Error(`WGSL V13 confirmation blueprint ${field} values must be unique.`);
    }
  }
  for (const blueprint of catalog.blueprints) {
    if (!['unary', 'binary'].includes(blueprint.arity)
      || typeof blueprint.brokenSpan !== 'string'
      || typeof blueprint.referenceSpan !== 'string'
      || blueprint.brokenSpan === blueprint.referenceSpan
      || typeof blueprint.mutationClass !== 'string') {
      throw new Error(`WGSL V13 confirmation blueprint is invalid: ${blueprint.id}.`);
    }
    if (blueprint.parameter != null) {
      if (typeof blueprint.parameter.name !== 'string'
        || !Array.isArray(blueprint.parameter.values)
        || blueprint.parameter.values.length < 2
        || blueprint.parameter.values.some((value) => !Number.isFinite(value))) {
        throw new Error(`WGSL V13 confirmation parameter is invalid: ${blueprint.id}.`);
      }
    }
  }
}

function entropyDigest(freezeCommit, blueprintId, purpose) {
  return sha256(`doppler-wgsl-v13-confirmation-v1\0${freezeCommit}\0${blueprintId}\0${purpose}`);
}

function digestUint32(digest, offset = 0) {
  return Number.parseInt(digest.slice(offset, offset + 8), 16) >>> 0;
}

function selectParameter(blueprint, freezeCommit) {
  if (blueprint.parameter == null) return {};
  const digest = entropyDigest(freezeCommit, blueprint.id, 'parameter');
  const values = blueprint.parameter.values;
  const value = values[digestUint32(digest) % values.length];
  return { [blueprint.parameter.name]: value };
}

function renderSource(blueprint) {
  const parameterName = blueprint.parameter?.name || 'reserved_0';
  const secondField = blueprint.parameter == null ? 'reserved_1' : 'reserved';
  const lines = [
    'override WORKGROUP_SIZE: u32 = 64u;',
    '',
    'struct Params {',
    '  length: u32,',
    '  output_offset: u32,',
    `  ${parameterName}: f32,`,
    `  ${secondField}: f32,`,
    '}',
    '',
  ];
  if (blueprint.arity === 'binary') {
    lines.push(
      '@group(0) @binding(0) var<storage, read> left_values: array<f32>;',
      '@group(0) @binding(1) var<storage, read> right_values: array<f32>;',
      '@group(0) @binding(2) var<storage, read_write> output_values: array<f32>;',
      '@group(0) @binding(3) var<uniform> params: Params;'
    );
  } else {
    lines.push(
      '@group(0) @binding(0) var<storage, read> input_values: array<f32>;',
      '@group(0) @binding(1) var<storage, read_write> output_values: array<f32>;',
      '@group(0) @binding(2) var<uniform> params: Params;'
    );
  }
  lines.push(
    '',
    '@compute @workgroup_size(WORKGROUP_SIZE)',
    'fn main(@builtin(global_invocation_id) global_id: vec3<u32>) {',
    '  let index = global_id.x;',
    '  if (index >= params.length) {',
    '    return;',
    '  }'
  );
  if (blueprint.arity === 'unary') lines.push('  let value = input_values[index];');
  lines.push(`  ${blueprint.brokenSpan}`, '}', '');
  return lines.join('\n');
}

function buildVariants(blueprint, freezeCommit) {
  const digest = entropyDigest(freezeCommit, blueprint.id, 'variants');
  const tailLength = 65 + (digestUint32(digest) % 15);
  const boundaryLength = 1 + (digestUint32(digest, 8) % 7);
  const prefix = blueprint.id.replace(/-f32$/, '');
  return [
    {
      shapeId: `confirm-${prefix}-nominal-64`,
      shapeClass: 'nominal',
      length: 64,
      workgroupId: 'wg-32',
      workgroupSize: 32,
    },
    {
      shapeId: `confirm-${prefix}-tail-${tailLength}`,
      shapeClass: 'non_workgroup_multiple',
      length: tailLength,
      workgroupId: 'wg-64',
      workgroupSize: 64,
    },
    {
      shapeId: `confirm-${prefix}-boundary-${boundaryLength}`,
      shapeClass: 'boundary_or_tail',
      length: boundaryLength,
      workgroupId: 'wg-32',
      workgroupSize: 32,
    },
  ];
}

function buildTask(blueprint, freezeCommit, fixtureDirectory, rank) {
  const source = renderSource(blueprint);
  const sourcePath = `${fixtureDirectory}/${blueprint.id}-broken.wgsl`;
  const seedDigest = entropyDigest(freezeCommit, blueprint.id, 'input-seed');
  const inputSeed = 30000 + rank * 1000 + (digestUint32(seedDigest) % 997);
  return {
    task: {
      taskId: `v13-confirmation-${blueprint.id}`,
      kernelFamilyId: `v13-confirmation-${blueprint.id.replace(/-f32$/, '')}`,
      sourcePath,
      sourceSha256: sha256(source),
      mutationClass: blueprint.mutationClass,
      brokenSpan: blueprint.brokenSpan,
      referenceSpan: blueprint.referenceSpan,
      oracleId: blueprint.oracleId,
      inputSeed,
      parameters: selectParameter(blueprint, freezeCommit),
      variants: buildVariants(blueprint, freezeCommit),
      metamorphicRelations: [
        'input_permutation_equivariance',
        'tiling_equivalence',
      ],
      materializationDigest: entropyDigest(freezeCommit, blueprint.id, 'task'),
    },
    source,
  };
}

function selectBlueprints(policy, catalog, freezeCommit) {
  const strata = policy?.selection?.strata;
  if (!Array.isArray(strata) || strata.length === 0) {
    throw new Error('WGSL V13 confirmation selection strata are required.');
  }
  const selected = [];
  for (const stratum of strata) {
    const eligible = catalog.blueprints
      .filter((blueprint) => (
        blueprint.arity === stratum.arity
        && (blueprint.parameter != null) === stratum.parameterized
      ))
      .map((blueprint) => ({
        blueprint,
        stratumId: stratum.id,
        rankDigest: entropyDigest(freezeCommit, blueprint.id, `rank:${stratum.id}`),
      }))
      .sort((left, right) => (
        left.rankDigest.localeCompare(right.rankDigest)
        || left.blueprint.id.localeCompare(right.blueprint.id)
      ));
    if (!Number.isInteger(stratum.count)
      || stratum.count < 1
      || eligible.length < stratum.count) {
      throw new Error(`WGSL V13 confirmation stratum is unsatisfied: ${stratum.id}.`);
    }
    selected.push(...eligible.slice(0, stratum.count));
  }
  if (new Set(selected.map(({ blueprint }) => blueprint.id)).size !== selected.length) {
    throw new Error('WGSL V13 confirmation strata selected a blueprint more than once.');
  }
  return selected.sort((left, right) => (
    left.rankDigest.localeCompare(right.rankDigest)
    || left.blueprint.id.localeCompare(right.blueprint.id)
  ));
}

export function buildWgslRepairV13ConfirmationPopulation(options) {
  const { policy, catalog, freezeCommit } = options;
  if (!COMMIT_PATTERN.test(freezeCommit)) {
    throw new Error('WGSL V13 confirmation freeze commit must be a full commit hash.');
  }
  requireBlueprintCatalog(catalog);
  const taskCount = Number(policy?.selection?.taskCount);
  if (!Number.isInteger(taskCount)
    || taskCount < 1
    || taskCount >= catalog.blueprints.length) {
    throw new Error('WGSL V13 confirmation task count must select a strict catalog subset.');
  }
  const selected = selectBlueprints(policy, catalog, freezeCommit);
  if (selected.length !== taskCount) {
    throw new Error('WGSL V13 confirmation strata do not sum to the frozen task count.');
  }
  const sources = {};
  const tasks = selected.map(({ blueprint, rankDigest, stratumId }, index) => {
    const built = buildTask(blueprint, freezeCommit, policy.outputs.fixtureDirectory, index);
    sources[built.task.sourcePath] = built.source;
    return {
      ...built.task,
      selectionRank: index + 1,
      selectionStratum: stratumId,
      selectionDigest: rankDigest,
    };
  });
  const manifest = {
    schema: 'doppler.wgsl-repair-semantic-task-manifest/v1',
    schemaVersion: 1,
    experimentId: 'doppler-wgsl-repair-v13',
    populationId: 'v13-semantic-seed-confirmation-v1',
    role: 'seed_confirmation',
    populationAuthority: 'selected_external20_seed_confirmation_only',
    responseContract: 'replacement_only_wgsl_span_v1',
    cpuOracleRevision: policy.oracleImplementation.revision,
    inputGeneratorRevision: 'wgsl-semantic-inputs-v1',
    materialization: {
      freezeCommit,
      algorithm: policy.selection.algorithm,
      generatorPath: policy.generator.path,
      generatorSha256: policy.generator.sha256,
      catalogPath: policy.catalog.path,
      catalogSha256: policy.catalog.sha256,
      oracleImplementationPath: policy.oracleImplementation.path,
      oracleImplementationSha256: policy.oracleImplementation.sha256,
      selectedBlueprintIds: selected.map(({ blueprint }) => blueprint.id),
      strata: policy.selection.strata,
      eligibleBlueprintCount: catalog.blueprints.length,
      selectedTaskCount: tasks.length,
      candidateInferenceBeforeFreeze: false,
    },
    tasks,
    sourceOverlapPolicy: 'No task identifier, kernel family, oracle identifier, source fixture, or input seed overlaps mechanics qualification, calibration, checkpoint selection, V12 training, V12 diagnostic, or V12 public evaluation.',
    claimBoundary: 'This commit-derived population may confirm or reject selected external20 seed 29 on disjoint semantic repairs. It cannot promote an adapter, authorize WGSL Doctor, or establish complete shader authorship.',
  };
  return { manifest, sources };
}

export async function materializeWgslRepairV13Confirmation(options) {
  const policyPath = options.policyPath || DEFAULT_POLICY;
  const [policy, policySha256] = await Promise.all([
    readJson(policyPath),
    sha256File(policyPath),
  ]);
  const catalog = await readJson(policy.catalog.path);
  requireFreezeCommit(options.freezeCommit);
  await Promise.all([
    verifyCommitBoundFile(
      options.freezeCommit,
      policyPath,
      policySha256,
      'confirmation materialization policy'
    ),
    verifyCommitBoundFile(
      options.freezeCommit,
      policy.generator.path,
      policy.generator.sha256,
      'confirmation generator'
    ),
    verifyCommitBoundFile(
      options.freezeCommit,
      policy.catalog.path,
      policy.catalog.sha256,
      'confirmation blueprint catalog'
    ),
    verifyCommitBoundFile(
      options.freezeCommit,
      policy.oracleImplementation.path,
      policy.oracleImplementation.sha256,
      'confirmation CPU oracle implementation'
    ),
  ]);
  const built = buildWgslRepairV13ConfirmationPopulation({
    policy,
    catalog,
    freezeCommit: options.freezeCommit,
  });
  for (const [sourcePath, source] of Object.entries(built.sources)) {
    await fs.mkdir(path.dirname(path.resolve(sourcePath)), { recursive: true });
    await fs.writeFile(path.resolve(sourcePath), source, 'utf8');
  }
  await fs.mkdir(path.dirname(path.resolve(policy.outputs.manifestPath)), { recursive: true });
  await fs.writeFile(
    path.resolve(policy.outputs.manifestPath),
    `${JSON.stringify(built.manifest, null, 2)}\n`,
    'utf8'
  );
  return {
    policyPath,
    policySha256,
    freezeCommit: options.freezeCommit,
    manifestPath: policy.outputs.manifestPath,
    manifestSha256: await sha256File(policy.outputs.manifestPath),
    taskCount: built.manifest.tasks.length,
    selectedBlueprintIds: built.manifest.materialization.selectedBlueprintIds,
  };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const receipt = await materializeWgslRepairV13Confirmation(args);
  process.stdout.write(`${JSON.stringify(receipt, null, 2)}\n`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(error instanceof Error ? error.stack : String(error));
    process.exitCode = 1;
  });
}
