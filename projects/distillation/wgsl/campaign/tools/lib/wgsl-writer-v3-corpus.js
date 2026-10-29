import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { dirname, join, relative, resolve } from 'node:path';

import { sha256Hex } from '../../src/utils/sha256.js';
import { buildWgslAuthorPrompt } from './wgsl-author-package.js';
import { WGSL_WRITER_V3_FAMILY_BUILDERS } from './wgsl-writer-v3-family-builders.js';
import { WGSL_WRITER_V3_MULTIPASS_FAMILY_BUILDERS } from './wgsl-writer-v3-multipass-families.js';
import { WGSL_WRITER_V3_RENDER_FAMILY_BUILDERS } from './wgsl-writer-v3-render-families.js';
import { WGSL_WRITER_V3_TEXTURE_FAMILY_BUILDERS } from './wgsl-writer-v3-texture-families.js';
import { evaluateWgslWriterV3Quality } from './wgsl-writer-v3-quality.js';
import { diversifyWgslWriterV3Package } from './wgsl-writer-v3-package-diversity.js';

const ROLE_FILENAMES = Object.freeze({
  training: 'train.jsonl',
  calibration: 'calibration.jsonl',
  checkpoint_selection: 'checkpoint-selection.jsonl',
  seed_confirmation: 'seed-confirmation.jsonl',
});

const BUILDERS = Object.freeze({
  ...WGSL_WRITER_V3_FAMILY_BUILDERS,
  ...WGSL_WRITER_V3_TEXTURE_FAMILY_BUILDERS,
  ...WGSL_WRITER_V3_RENDER_FAMILY_BUILDERS,
  ...WGSL_WRITER_V3_MULTIPASS_FAMILY_BUILDERS,
});

function isPlainObject(value) {
  return value != null && typeof value === 'object' && !Array.isArray(value);
}

function stablePath(repoRoot, filePath) {
  return relative(repoRoot, filePath).replaceAll('\\', '/');
}

function toJsonl(rows) {
  return `${rows.map((row) => JSON.stringify(row)).join('\n')}\n`;
}

function taskId(family, rowIndex) {
  return [
    'writer-v3',
    family.populationRole.replaceAll('_', '-'),
    family.id,
    String(rowIndex + 1).padStart(3, '0'),
  ].join('-');
}

function variationSignature(task, variation) {
  if (variation === 'workgroup') return JSON.stringify(task.context.overrides);
  if (variation === 'dispatch') {
    return JSON.stringify({
      parameters: task.context.parameters,
      overrides: task.context.overrides,
      dispatches: task.packageValue.passes
        .filter((pass) => pass.kind === 'compute')
        .map((pass) => pass.dispatch),
    });
  }
  if (variation === 'draw') {
    return JSON.stringify({
      parameters: task.context.parameters,
      draws: task.packageValue.passes
        .filter((pass) => pass.kind === 'render')
        .map((pass) => pass.draw),
    });
  }
  if (variation === 'texture_size') {
    return JSON.stringify({
      width: task.context.parameters.width,
      height: task.context.parameters.height,
    });
  }
  if (variation === 'instance_count') {
    return String(task.context.parameters.instanceCount);
  }
  if (variation === 'vertex_count') {
    return JSON.stringify({
      vertexBytes: task.context.parameters.vertexBytes,
      indexCount: task.context.parameters.indexCount,
      draws: task.packageValue.passes
        .filter((pass) => pass.kind === 'render')
        .map((pass) => pass.draw),
    });
  }
  return JSON.stringify(task.context.parameters);
}

function materializeTask(family, rowIndex) {
  const builder = BUILDERS[family.id];
  if (typeof builder !== 'function') {
    throw new Error(`WGSL writer v3 family builder is missing: ${family.id}.`);
  }
  const built = builder(family, rowIndex);
  if (family.populationRole === 'training' && family.packageDiversity !== null) {
    built.packageValue = diversifyWgslWriterV3Package(
      built.packageValue,
      rowIndex,
      family.packageDiversity
    );
  }
  const quality = evaluateWgslWriterV3Quality(built, family);
  if (!quality.pass) {
    throw new Error(
      `WGSL writer v3 quality gate failed for ${family.id}: ${quality.violations.join(', ')}.`
    );
  }
  return {
    schema: 'doppler.wgsl-writer-v3-task/v1',
    taskId: taskId(family, rowIndex),
    semanticFamilyId: family.id,
    populationRole: family.populationRole,
    pipelineKind: family.pipelineKind,
    taskClass: family.taskClass,
    semanticContract: family.semanticContract,
    source: {
      owner: 'doppler',
      license: 'Apache-2.0',
      lineage: family.sourceLineage,
    },
    objective: built.objective,
    contract: built.contract,
    context: built.context,
    acceptance: built.acceptance,
    packageValue: built.packageValue,
    packageSha256: sha256Hex(JSON.stringify(built.packageValue)),
    oracle: built.oracle,
    oracleSha256: sha256Hex(JSON.stringify(built.oracle)),
    quality,
    variations: Object.fromEntries(family.verification.requiredVariations.map((variation) => [
      variation,
      variationSignature(built, variation),
    ])),
    historicalRegressions: [
      'tail_dispatch_oob',
      'binding_contract_drift',
      'pass_order_or_draw_omission',
      'output_readback_or_cleanup_loss',
    ],
  };
}

function promptTask(task) {
  return {
    taskId: task.taskId,
    objective: task.objective,
    semanticContract: task.semanticContract,
    resources: task.contract.resources,
    parameters: task.contract.parameterNames,
    acceptance: task.acceptance,
    limits: task.contract.limits || {},
  };
}

function buildCorpusPrompt(task, promptContract) {
  let prompt = buildWgslAuthorPrompt(promptTask(task), promptContract);
  if (promptContract.includesExplicitSemanticContract !== true) return prompt;
  if (!isPlainObject(task.semanticContract)) {
    throw new Error(`WGSL writer v3 task is missing semantic contract: ${task.taskId}.`);
  }
  const boundary = '</objective>\n<host_contract>';
  if (!prompt.includes(boundary)) {
    throw new Error('WGSL writer v3 semantic prompt objective boundary is missing.');
  }
  prompt = prompt.replace(boundary, [
    '</objective>',
    '<semantic_contract>',
    JSON.stringify(task.semanticContract, null, 2),
    '</semantic_contract>',
    '<host_contract>',
  ].join('\n'));
  if (promptContract.includesExplicitOutputTokenBudget !== true) return prompt;
  const outputTokenBudget = Number(promptContract.outputTokenBudget);
  if (!Number.isSafeInteger(outputTokenBudget) || outputTokenBudget < 1
    || promptContract.hardStopDisclosed !== true) {
    throw new Error('WGSL writer v3 explicit output-token budget contract is invalid.');
  }
  const responseBoundary = '</host_contract>';
  if (!prompt.endsWith(responseBoundary)) {
    throw new Error('WGSL writer v3 output-budget response boundary is missing.');
  }
  return prompt.replace(responseBoundary, [
    '</host_contract>',
    '<output_contract>',
    `The response is hard-stopped after ${outputTokenBudget} generated tokens.`,
    `Complete the single JSON object within ${outputTokenBudget} generated tokens.`,
    '</output_contract>',
  ].join('\n'));
}

function rowForTask(task, policy) {
  const prompt = buildCorpusPrompt(task, policy.promptContract);
  const completion = JSON.stringify(task.packageValue);
  return {
    schema: 'doppler.wgsl-writer-v3-sft-row/v1',
    schemaVersion: 1,
    rowId: task.taskId,
    taskId: task.taskId,
    populationRole: task.populationRole,
    semanticFamilyId: task.semanticFamilyId,
    pipelineKind: task.pipelineKind,
    sourceOwner: task.source.owner,
    sourceLicense: task.source.license,
    sourceLineage: task.source.lineage,
    prompt,
    promptSha256: sha256Hex(prompt),
    completion,
    completionSha256: sha256Hex(completion),
    packageSha256: task.packageSha256,
    qualityPass: task.quality.pass,
  };
}

function roleManifest(policy, role, tasks) {
  return {
    schema: 'doppler.wgsl-writer-v3-task-manifest/v1',
    schemaVersion: 1,
    source: 'doppler',
    experimentId: policy.experimentId,
    role,
    populationAuthority: role,
    responseContract: 'doppler.wgsl-author-package/v1',
    sourceLicense: 'Apache-2.0',
    tasks,
    claimBoundary: `${role} tasks provide family-disjoint development evidence only; they do not provide external promotion authority.`,
  };
}

function verifyFamilyVariation(tasks, family) {
  for (const variation of family.verification.requiredVariations) {
    const values = new Set(tasks.map((task) => task.variations[variation]));
    if (values.size < 2) {
      throw new Error(`${family.id} does not vary ${variation} across its materialized tasks.`);
    }
  }
}

function overlapReport(tasksByRole) {
  const roles = Object.keys(tasksByRole);
  const overlaps = [];
  for (let left = 0; left < roles.length; left += 1) {
    for (let right = left + 1; right < roles.length; right += 1) {
      const leftFamilies = new Set(tasksByRole[roles[left]].map((task) => task.semanticFamilyId));
      const shared = [...new Set(tasksByRole[roles[right]].map((task) => task.semanticFamilyId))]
        .filter((family) => leftFamilies.has(family));
      if (shared.length > 0) overlaps.push({ left: roles[left], right: roles[right], shared });
    }
  }
  return overlaps;
}

export function materializeWgslWriterV3Corpus(options) {
  const repoRoot = resolve(options.repoRoot);
  const outputRoot = resolve(options.outputRoot);
  const { policy, catalog } = options;
  if (!isPlainObject(policy?.corpus?.rowsPerFamily)
    || !Array.isArray(catalog?.families)
    || catalog.families.length !== 20) {
    throw new Error('WGSL writer v3 corpus policy and capability catalog are required.');
  }
  const tasksByRole = Object.fromEntries(Object.keys(ROLE_FILENAMES).map((role) => [role, []]));
  for (const family of catalog.families) {
    const count = Number(policy.corpus.rowsPerFamily[family.populationRole]);
    if (!Number.isSafeInteger(count) || count < 3) {
      throw new Error(`WGSL writer v3 row count is invalid for ${family.populationRole}.`);
    }
    const materializationFamily = {
      ...family,
      sourceLineage: policy.corpus.sourceLineage,
      packageDiversity: family.populationRole === 'training'
        ? policy.corpus.packageDiversity || null
        : null,
    };
    const familyTasks = Array.from(
      { length: count },
      (_, index) => materializeTask(materializationFamily, index)
    );
    verifyFamilyVariation(familyTasks, family);
    tasksByRole[family.populationRole].push(...familyTasks);
  }
  const overlaps = overlapReport(tasksByRole);
  if (overlaps.length > 0) {
    throw new Error(`WGSL writer v3 semantic-family leakage: ${JSON.stringify(overlaps)}.`);
  }
  const files = new Map();
  const roleBindings = {};
  const rowsByRole = {};
  const manifests = {};
  for (const [role, tasks] of Object.entries(tasksByRole)) {
    const rows = tasks.map((task) => rowForTask(task, policy));
    rowsByRole[role] = rows;
    const datasetPath = join(outputRoot, ROLE_FILENAMES[role]);
    files.set(datasetPath, toJsonl(rows));
    if (role !== 'training') {
      const manifest = roleManifest(policy, role, tasks);
      const manifestPath = join(outputRoot, `${role.replaceAll('_', '-')}.tasks.json`);
      files.set(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`);
      manifests[role] = { manifest, path: stablePath(repoRoot, manifestPath) };
    }
    roleBindings[role] = {
      rows: rows.length,
      semanticFamilies: new Set(tasks.map((task) => task.semanticFamilyId)).size,
      datasetPath: stablePath(repoRoot, datasetPath),
      datasetSha256: sha256Hex(toJsonl(rows)),
      ...(manifests[role] ? { taskManifestPath: manifests[role].path } : {}),
    };
  }
  const trainingRepresentatives = policy.referenceQualification.executeEveryTrainingTask === true
    ? tasksByRole.training
    : tasksByRole.training.filter((task, index, tasks) => (
      tasks.findIndex((candidate) => candidate.semanticFamilyId === task.semanticFamilyId) === index
    ));
  const qualificationManifest = roleManifest(policy, 'reference_qualification_only', [
    ...trainingRepresentatives,
    ...Object.values(manifests).flatMap(({ manifest }) => manifest.tasks),
  ]);
  qualificationManifest.populationAuthority = 'none';
  qualificationManifest.claimBoundary = 'Reference qualification proves the materialized human-authored packages and oracles, not model capability.';
  const qualificationPath = join(outputRoot, 'reference-qualification.tasks.json');
  files.set(qualificationPath, `${JSON.stringify(qualificationManifest, null, 2)}\n`);

  const allRows = Object.values(rowsByRole).flat();
  const duplicateRowIds = allRows.length - new Set(allRows.map((row) => row.rowId)).size;
  const duplicatePrompts = allRows.length - new Set(allRows.map((row) => row.promptSha256)).size;
  if (duplicateRowIds !== 0 || duplicatePrompts !== 0) {
    throw new Error('WGSL writer v3 corpus contains duplicate row ids or prompts.');
  }
  const fileBindings = Object.fromEntries([...files.entries()]
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([filePath, contents]) => [stablePath(repoRoot, filePath), {
      sha256: sha256Hex(contents),
      bytes: Buffer.byteLength(contents),
    }]));
  const manifestCore = {
    schema: 'doppler.wgsl-writer-v3-corpus-manifest/v1',
    schemaVersion: 1,
    source: 'doppler',
    experimentId: policy.experimentId,
    policy: { path: options.policyPath, sha256: options.policySha256 },
    capabilityCatalog: { path: options.catalogPath, sha256: options.catalogSha256 },
    outputRoot: stablePath(repoRoot, outputRoot),
    roles: roleBindings,
    referenceQualification: {
      taskManifestPath: stablePath(repoRoot, qualificationPath),
      tasks: qualificationManifest.tasks.length,
      replayCount: policy.referenceQualification.replayCount,
    },
    isolation: {
      splitKey: 'semanticFamilyId',
      semanticFamilyOverlaps: overlaps,
      duplicateRowIds,
      duplicatePrompts,
      externalPromotionPopulationIncluded: false,
    },
    quality: {
      blocking: true,
      styleGuide: 'docs/style/wgsl-style-guide.md',
      allReferencePackagesPass: Object.values(tasksByRole)
        .flat()
        .every((task) => task.quality.pass),
    },
    fileBindings,
    corpusSha256: sha256Hex(JSON.stringify(
      Object.values(rowsByRole).flat().map((row) => [row.rowId, row.promptSha256, row.completionSha256])
    )),
    claimBoundary: policy.claimBoundary,
  };
  const manifest = {
    ...manifestCore,
    manifestSha256: sha256Hex(JSON.stringify(manifestCore)),
  };
  const manifestPath = join(outputRoot, 'corpus-manifest.json');
  files.set(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`);
  return {
    files,
    manifest,
    manifestPath,
    rowsByRole,
    tasksByRole,
    qualificationManifest,
  };
}

export async function writeWgslWriterV3Corpus(materialized) {
  for (const [filePath, contents] of materialized.files) {
    await mkdir(dirname(filePath), { recursive: true });
    await writeFile(filePath, contents, 'utf8');
  }
  return { writtenFiles: materialized.files.size };
}

export async function checkWgslWriterV3Corpus(materialized) {
  const mismatches = [];
  for (const [filePath, expected] of materialized.files) {
    let actual;
    try {
      actual = await readFile(filePath, 'utf8');
    } catch {
      mismatches.push(`${filePath}:missing`);
      continue;
    }
    if (actual !== expected) mismatches.push(`${filePath}:drift`);
  }
  if (mismatches.length > 0) {
    throw new Error(`WGSL writer v3 corpus drift:\n${mismatches.join('\n')}`);
  }
  return { checkedFiles: materialized.files.size };
}
