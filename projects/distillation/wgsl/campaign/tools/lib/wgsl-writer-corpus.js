import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { dirname, join, relative, resolve } from 'node:path';

import { sha256Hex } from '../../src/utils/sha256.js';
import { buildWgslWriterPrompt } from './wgsl-writer-semantic-harness.js';

const ROLE_FILENAMES = Object.freeze({
  training: 'train.jsonl',
  calibration: 'calibration.jsonl',
  checkpoint_selection: 'checkpoint-selection.jsonl',
  seed_confirmation: 'seed-confirmation.jsonl',
});

const IDENTIFIER_SCHEMES = Object.freeze([
  {
    paramsType: 'Params',
    params: 'params',
    length: 'length',
    outputOffset: 'output_offset',
    input: 'input_values',
    left: 'left_values',
    right: 'right_values',
    output: 'output_values',
    gid: 'global_id',
    index: 'index',
    result: 'result',
  },
  {
    paramsType: 'Config',
    params: 'config',
    length: 'element_count',
    outputOffset: 'destination_offset',
    input: 'source_values',
    left: 'lhs_values',
    right: 'rhs_values',
    output: 'destination_values',
    gid: 'invocation_id',
    index: 'element_index',
    result: 'computed_value',
  },
  {
    paramsType: 'Uniforms',
    params: 'uniforms',
    length: 'logical_size',
    outputOffset: 'write_offset',
    input: 'input_data',
    left: 'a_values',
    right: 'b_values',
    output: 'result_data',
    gid: 'dispatch_id',
    index: 'idx',
    result: 'value',
  },
  {
    paramsType: 'Settings',
    params: 'settings',
    length: 'item_count',
    outputOffset: 'result_offset',
    input: 'values',
    left: 'first_values',
    right: 'second_values',
    output: 'results',
    gid: 'global_invocation',
    index: 'logical_index',
    result: 'output_value',
  },
  {
    paramsType: 'Parameters',
    params: 'parameters',
    length: 'value_count',
    outputOffset: 'output_start',
    input: 'samples',
    left: 'primary_values',
    right: 'secondary_values',
    output: 'outputs',
    gid: 'global_id',
    index: 'item_index',
    result: 'transformed',
  },
  {
    paramsType: 'KernelParams',
    params: 'kernel_params',
    length: 'num_elements',
    outputOffset: 'destination_start',
    input: 'source',
    left: 'left',
    right: 'right',
    output: 'destination',
    gid: 'invocation',
    index: 'linear_index',
    result: 'computed',
  },
  {
    paramsType: 'DispatchParams',
    params: 'dispatch_params',
    length: 'active_length',
    outputOffset: 'output_base',
    input: 'input_buffer',
    left: 'x_values',
    right: 'y_values',
    output: 'output_buffer',
    gid: 'global_position',
    index: 'position',
    result: 'answer',
  },
  {
    paramsType: 'Control',
    params: 'control',
    length: 'logical_length',
    outputOffset: 'store_offset',
    input: 'operands',
    left: 'left_operands',
    right: 'right_operands',
    output: 'result_values',
    gid: 'invocation_id',
    index: 'offset',
    result: 'operation_result',
  },
]);

const WORKGROUP_DEFAULTS = Object.freeze([32, 64, 128, 256]);
const SUPPORTED_ORACLES = new Set([
  'absolute_f32',
  'add_scalar_f32',
  'cap_f32',
  'difference_scale_f32',
  'distance_pair_f32',
  'floor_f32',
  'leaky_relu_f32',
  'mask_below_f32',
  'max_pair_f32',
  'mean_pair_f32',
  'min_pair_f32',
  'mix_f32',
  'multiply_pair_f32',
  'negate_f32',
  'relu_f32',
  'saxpy_f32',
  'scale_f32',
  'square_bias_f32',
  'square_scale_f32',
  'subtract_f32',
  'threshold_negate_f32',
]);

function isPlainObject(value) {
  return value != null && typeof value === 'object' && !Array.isArray(value);
}

function requireString(value, label) {
  const normalized = typeof value === 'string' ? value.trim() : '';
  if (!normalized) throw new Error(`${label} is required.`);
  return normalized;
}

function requirePositiveInteger(value, label) {
  const parsed = Number(value);
  if (!Number.isInteger(parsed) || parsed < 1) {
    throw new Error(`${label} must be an integer >= 1.`);
  }
  return parsed;
}

function stablePath(repoRoot, filePath) {
  return relative(repoRoot, filePath).replaceAll('\\', '/');
}

function toJsonl(rows) {
  return `${rows.map((row) => JSON.stringify(row)).join('\n')}\n`;
}

function replaceExpression(expression, identifiers, blueprint) {
  const replacements = {
    '$input': `${identifiers.input}[${identifiers.index}]`,
    '$left': `${identifiers.left}[${identifiers.index}]`,
    '$right': `${identifiers.right}[${identifiers.index}]`,
    '$first': `${identifiers.params}.${blueprint.firstField}`,
  };
  let rendered = expression;
  for (const [placeholder, value] of Object.entries(replacements)) {
    rendered = rendered.replaceAll(placeholder, value);
  }
  if (/\$[a-z]+/.test(rendered)) {
    throw new Error(`Unresolved expression placeholder in ${blueprint.id}: ${rendered}`);
  }
  return rendered;
}

function renderShader(blueprint, identifiers, workgroupDefault) {
  const inputs = blueprint.arity === 'binary'
    ? [
      `@group(0) @binding(0) var<storage, read> ${identifiers.left}: array<f32>;`,
      `@group(0) @binding(1) var<storage, read> ${identifiers.right}: array<f32>;`,
    ]
    : [`@group(0) @binding(0) var<storage, read> ${identifiers.input}: array<f32>;`];
  const outputBinding = blueprint.arity === 'binary' ? 2 : 1;
  const paramsBinding = blueprint.arity === 'binary' ? 3 : 2;
  const expression = replaceExpression(blueprint.expression, identifiers, blueprint);
  return [
    `override WORKGROUP_SIZE: u32 = ${workgroupDefault}u;`,
    '',
    `struct ${identifiers.paramsType} {`,
    `    ${identifiers.length}: u32,`,
    `    ${identifiers.outputOffset}: u32,`,
    `    ${blueprint.firstField}: f32,`,
    '    second_reserved: f32,',
    '}',
    '',
    ...inputs,
    `@group(0) @binding(${outputBinding}) var<storage, read_write> ${identifiers.output}: array<f32>;`,
    `@group(0) @binding(${paramsBinding}) var<uniform> ${identifiers.params}: ${identifiers.paramsType};`,
    '',
    '@compute @workgroup_size(WORKGROUP_SIZE, 1, 1)',
    `fn main(@builtin(global_invocation_id) ${identifiers.gid}: vec3<u32>) {`,
    `    let ${identifiers.index} = ${identifiers.gid}.x;`,
    `    if (${identifiers.index} >= ${identifiers.params}.${identifiers.length}) {`,
    '        return;',
    '    }',
    '',
    `    let ${identifiers.result} = ${expression};`,
    `    ${identifiers.output}[${identifiers.params}.${identifiers.outputOffset} + ${identifiers.index}] = ${identifiers.result};`,
    '}',
    '',
  ].join('\n');
}

function buildBindings(blueprint, identifiers) {
  const bindings = blueprint.arity === 'binary'
    ? [
      {
        group: 0,
        binding: 0,
        name: identifiers.left,
        kind: 'read_only_storage',
        wgslType: 'array<f32>',
      },
      {
        group: 0,
        binding: 1,
        name: identifiers.right,
        kind: 'read_only_storage',
        wgslType: 'array<f32>',
      },
    ]
    : [{
      group: 0,
      binding: 0,
      name: identifiers.input,
      kind: 'read_only_storage',
      wgslType: 'array<f32>',
    }];
  const outputBinding = blueprint.arity === 'binary' ? 2 : 1;
  const paramsBinding = blueprint.arity === 'binary' ? 3 : 2;
  bindings.push(
    {
      group: 0,
      binding: outputBinding,
      name: identifiers.output,
      kind: 'read_write_storage',
      wgslType: 'array<f32>',
    },
    {
      group: 0,
      binding: paramsBinding,
      name: identifiers.params,
      kind: 'uniform',
      wgslType: identifiers.paramsType,
    }
  );
  return bindings;
}

function specificationFor(blueprint, identifiers, variant) {
  const operation = blueprint.operationDescription;
  const store = `store the result in ${identifiers.output}[${identifiers.params}.${identifiers.outputOffset} + index]`;
  const bounds = `An invocation whose x index is at least ${identifiers.params}.${identifiers.length} must return before any storage access`;
  const templates = [
    `For every logical index, ${operation}, then ${store}. ${bounds}.`,
    `Implement an elementwise f32 compute kernel: ${operation}. Process exactly ${identifiers.params}.${identifiers.length} elements, ${store}, and perform no storage access for an out-of-range invocation.`,
    `At each in-range global x index, ${operation} and ${store}. ${bounds}; output prefix and tail elements must remain untouched.`,
    `The shader operates on one logical f32 element per global x invocation. It must ${operation}, ${store}, and guard all reads and writes with the declared logical length.`,
  ];
  return templates[variant % templates.length];
}

function interfaceFor(blueprint, identifiers, workgroupDefault) {
  return {
    entryPoint: 'main',
    stage: 'compute',
    requiredOverrides: [{
      name: 'WORKGROUP_SIZE',
      type: 'u32',
      default: workgroupDefault,
    }],
    bindings: buildBindings(blueprint, identifiers),
    uniformLayout: [
      { name: identifiers.length, type: 'u32', byteOffset: 0 },
      { name: identifiers.outputOffset, type: 'u32', byteOffset: 4 },
      { name: blueprint.firstField, type: 'f32', byteOffset: 8 },
      { name: 'second_reserved', type: 'f32', byteOffset: 12 },
    ],
    dispatch: `ceil(${identifiers.params}.${identifiers.length} / WORKGROUP_SIZE) workgroups in x; y=1; z=1`,
    requiredBuiltin: 'global_invocation_id',
    boundsRule: `Return when global_invocation_id.x >= ${identifiers.params}.${identifiers.length}.`,
    outputRule: `Write only ${identifiers.output}[${identifiers.params}.${identifiers.outputOffset} + index].`,
  };
}

function taskSeed(taskId) {
  return Number.parseInt(sha256Hex(`input-seed:${taskId}`).slice(0, 7), 16) + 1;
}

function taskVariants(taskId) {
  return [
    {
      shapeId: `${taskId}-nominal-64`,
      shapeClass: 'nominal',
      length: 64,
      workgroupId: 'wg-32',
      workgroupSize: 32,
    },
    {
      shapeId: `${taskId}-tail-67`,
      shapeClass: 'non_workgroup_multiple',
      length: 67,
      workgroupId: 'wg-64',
      workgroupSize: 64,
    },
    {
      shapeId: `${taskId}-boundary-1`,
      shapeClass: 'boundary_or_tail',
      length: 1,
      workgroupId: 'wg-32',
      workgroupSize: 32,
    },
  ];
}

function buildTask(blueprint, blueprintIndex, rowIndex) {
  const identifiers = IDENTIFIER_SCHEMES[rowIndex % IDENTIFIER_SCHEMES.length];
  const workgroupDefault = WORKGROUP_DEFAULTS[
    (rowIndex + blueprintIndex) % WORKGROUP_DEFAULTS.length
  ];
  const taskId = [
    'writer-v2',
    blueprint.role.replaceAll('_', '-'),
    blueprint.id.replaceAll('_', '-'),
    String(rowIndex + 1).padStart(3, '0'),
  ].join('-');
  const specificationVariant = (rowIndex * 3 + blueprintIndex) % 4;
  const specification = specificationFor(blueprint, identifiers, specificationVariant);
  const interfaceContract = interfaceFor(blueprint, identifiers, workgroupDefault);
  const referenceShader = renderShader(blueprint, identifiers, workgroupDefault);
  return {
    taskId,
    kernelFamilyId: `writer-v2-${blueprint.id.replaceAll('_', '-')}`,
    semanticFamilyId: blueprint.oracleId,
    populationRole: blueprint.role,
    blueprintId: blueprint.id,
    specification,
    interfaceContract,
    referenceShader,
    referenceShaderSha256: sha256Hex(referenceShader),
    oracleId: blueprint.oracleId,
    inputSeed: taskSeed(taskId),
    parameters: blueprint.parameters,
    variants: taskVariants(taskId),
    metamorphicRelations: [
      'input_permutation_equivariance',
      'tiling_equivalence',
    ],
  };
}

function taskForManifest(task, referenceShaderPath) {
  const { referenceShader, semanticFamilyId, populationRole, blueprintId, ...manifestTask } = task;
  return {
    ...manifestTask,
    semanticFamilyId,
    populationRole,
    blueprintId,
    referenceShaderPath,
  };
}

function rowForTask(task, promptContract, catalog) {
  const prompt = buildWgslWriterPrompt(task, promptContract);
  return {
    schema: 'doppler.wgsl-writer-sft-row/v1',
    schemaVersion: 1,
    rowId: task.taskId,
    taskId: task.taskId,
    taskContract: promptContract.responseContract,
    populationRole: task.populationRole,
    semanticFamilyId: task.semanticFamilyId,
    kernelFamilyId: task.kernelFamilyId,
    blueprintId: task.blueprintId,
    sourceId: catalog.catalogId,
    sourceLicense: catalog.license,
    sourceLineage: 'doppler_owned_parametric_blueprint',
    prompt,
    promptSha256: sha256Hex(prompt),
    completion: task.referenceShader.trim(),
    completionSha256: sha256Hex(task.referenceShader.trim()),
    referenceShaderSha256: task.referenceShaderSha256,
  };
}

export function validateWgslWriterBlueprintCatalog(catalog) {
  if (!isPlainObject(catalog)
    || catalog.schemaVersion !== 1
    || catalog.source !== 'doppler'
    || !Array.isArray(catalog.blueprints)
    || catalog.blueprints.length === 0) {
    throw new Error('WGSL writer blueprint catalog must be a non-empty Doppler v1 catalog.');
  }
  const ids = new Set();
  const oracles = new Set();
  const excluded = new Set(catalog.excludedOracleIds || []);
  for (const [index, blueprint] of catalog.blueprints.entries()) {
    const id = requireString(blueprint?.id, `blueprints[${index}].id`);
    const oracleId = requireString(blueprint?.oracleId, `blueprints[${index}].oracleId`);
    if (ids.has(id)) throw new Error(`Duplicate WGSL writer blueprint id: ${id}`);
    if (oracles.has(oracleId)) throw new Error(`Duplicate WGSL writer oracle: ${oracleId}`);
    if (excluded.has(oracleId)) throw new Error(`Excluded writer oracle was assigned: ${oracleId}`);
    if (!SUPPORTED_ORACLES.has(oracleId)) {
      throw new Error(`WGSL writer oracle is not supported by the frozen harness: ${oracleId}`);
    }
    if (!Object.hasOwn(ROLE_FILENAMES, blueprint.role)) {
      throw new Error(`Unsupported WGSL writer population role: ${blueprint.role}`);
    }
    if (!['unary', 'binary'].includes(blueprint.arity)) {
      throw new Error(`Unsupported WGSL writer arity: ${blueprint.arity}`);
    }
    requireString(blueprint.operationDescription, `${id}.operationDescription`);
    requireString(blueprint.expression, `${id}.expression`);
    requireString(blueprint.firstField, `${id}.firstField`);
    const parameters = isPlainObject(blueprint.parameters) ? blueprint.parameters : null;
    if (!parameters) throw new Error(`${id}.parameters must be an object.`);
    if (blueprint.firstParameterKey === null) {
      if (Object.keys(parameters).length !== 0) {
        throw new Error(`${id} has parameters without firstParameterKey.`);
      }
    } else if (!Object.hasOwn(parameters, blueprint.firstParameterKey)) {
      throw new Error(`${id} is missing parameter ${blueprint.firstParameterKey}.`);
    }
    ids.add(id);
    oracles.add(oracleId);
  }
  return catalog;
}

function populationManifest(experimentId, role, tasks) {
  return {
    schema: 'doppler.wgsl-writer-task-manifest/v1',
    schemaVersion: 1,
    experimentId,
    role,
    populationAuthority: role,
    responseContract: 'complete_wgsl_compute_shader_only_v1',
    cpuOracleRevision: 'wgsl-semantic-cpu-oracles-v1',
    inputGeneratorRevision: 'wgsl-semantic-inputs-v1',
    tasks,
    overlapPolicy: 'Semantic families, task ids, prompts, reference shaders, and input seeds are disjoint across writer-v2 population roles.',
    claimBoundary: `${role} evidence is limited to the frozen complete 1-D elementwise f32 writer contract.`,
  };
}

function overlapPairs(roleFamilies) {
  const roles = Object.keys(roleFamilies);
  const overlaps = [];
  for (let left = 0; left < roles.length; left += 1) {
    for (let right = left + 1; right < roles.length; right += 1) {
      const shared = roleFamilies[roles[left]].filter((family) => (
        roleFamilies[roles[right]].includes(family)
      ));
      if (shared.length > 0) {
        overlaps.push({ left: roles[left], right: roles[right], semanticFamilies: shared });
      }
    }
  }
  return overlaps;
}

export function materializeWgslWriterCorpus(options) {
  const repoRoot = resolve(options.repoRoot);
  const outputRoot = resolve(options.outputRoot);
  const catalog = validateWgslWriterBlueprintCatalog(options.catalog);
  const policy = options.policy;
  if (!isPlainObject(policy?.corpus?.rowsPerFamily)
    || !isPlainObject(policy?.promptContract)) {
    throw new Error('WGSL writer corpus policy is incomplete.');
  }
  const tasksByRole = Object.fromEntries(Object.keys(ROLE_FILENAMES).map((role) => [role, []]));
  for (const [blueprintIndex, blueprint] of catalog.blueprints.entries()) {
    const rowCount = requirePositiveInteger(
      policy.corpus.rowsPerFamily[blueprint.role],
      `corpus.rowsPerFamily.${blueprint.role}`
    );
    for (let rowIndex = 0; rowIndex < rowCount; rowIndex += 1) {
      tasksByRole[blueprint.role].push(buildTask(blueprint, blueprintIndex, rowIndex));
    }
  }

  const files = new Map();
  const rowsByRole = {};
  const manifests = {};
  for (const [role, tasks] of Object.entries(tasksByRole)) {
    const rows = tasks.map((task) => rowForTask(task, policy.promptContract, catalog));
    rowsByRole[role] = rows;
    const datasetPath = join(outputRoot, ROLE_FILENAMES[role]);
    files.set(datasetPath, toJsonl(rows));
    if (role === 'training') continue;
    const manifestTasks = tasks.map((task) => {
      const referencePath = join(outputRoot, 'references', role, `${task.taskId}.wgsl`);
      files.set(referencePath, task.referenceShader);
      return taskForManifest(task, stablePath(repoRoot, referencePath));
    });
    const manifest = populationManifest(policy.experimentId, role, manifestTasks);
    const manifestPath = join(outputRoot, `${role.replaceAll('_', '-')}.tasks.json`);
    files.set(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`);
    manifests[role] = {
      manifest,
      path: stablePath(repoRoot, manifestPath),
    };
  }

  const trainingRepresentatives = [];
  const trainingFamilies = new Set();
  for (const task of tasksByRole.training) {
    if (trainingFamilies.has(task.semanticFamilyId)) continue;
    trainingFamilies.add(task.semanticFamilyId);
    const referencePath = join(
      outputRoot,
      'references',
      'qualification-training',
      `${task.taskId}.wgsl`
    );
    files.set(referencePath, task.referenceShader);
    trainingRepresentatives.push(taskForManifest(task, stablePath(repoRoot, referencePath)));
  }
  const qualificationTasks = [
    ...trainingRepresentatives,
    ...Object.values(manifests).flatMap(({ manifest }) => manifest.tasks),
  ];
  const qualificationManifest = populationManifest(
    policy.experimentId,
    'reference_qualification_only',
    qualificationTasks
  );
  qualificationManifest.populationAuthority = 'none';
  qualificationManifest.claimBoundary = 'Reference qualification establishes generated-corpus compilation and semantic harness mechanics only; it contains no model output.';
  const qualificationPath = join(outputRoot, 'reference-qualification.tasks.json');
  files.set(qualificationPath, `${JSON.stringify(qualificationManifest, null, 2)}\n`);

  const roleFamilies = Object.fromEntries(Object.entries(tasksByRole).map(([role, tasks]) => [
    role,
    [...new Set(tasks.map((task) => task.semanticFamilyId))].sort(),
  ]));
  const overlaps = overlapPairs(roleFamilies);
  if (overlaps.length > 0) {
    throw new Error(`WGSL writer semantic-family leakage: ${JSON.stringify(overlaps)}`);
  }
  const allRows = Object.values(rowsByRole).flat();
  const rowIds = new Set(allRows.map((row) => row.rowId));
  const promptHashes = new Set(allRows.map((row) => row.promptSha256));
  if (rowIds.size !== allRows.length || promptHashes.size !== allRows.length) {
    throw new Error('WGSL writer corpus contains duplicate row ids or prompts.');
  }
  const fileBindings = Object.fromEntries([...files.entries()]
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([filePath, contents]) => [stablePath(repoRoot, filePath), {
      sha256: sha256Hex(contents),
      bytes: Buffer.byteLength(contents),
    }]));
  const manifestCore = {
    artifactType: 'wgsl_writer_corpus_manifest',
    schemaVersion: 1,
    experimentId: policy.experimentId,
    taskScope: catalog.taskScope,
    taskContract: policy.promptContract.responseContract,
    catalog: {
      path: policy.corpus.blueprintCatalog.path,
      sha256: policy.corpus.blueprintCatalog.sha256,
      catalogId: catalog.catalogId,
      license: catalog.license,
      lineage: 'doppler_owned_parametric_blueprints',
    },
    constructionPolicy: {
      path: options.policyPath,
      sha256: options.policySha256,
    },
    roles: Object.fromEntries(Object.entries(rowsByRole).map(([role, rows]) => [role, {
      datasetPath: stablePath(repoRoot, join(outputRoot, ROLE_FILENAMES[role])),
      rows: rows.length,
      semanticFamilies: roleFamilies[role],
      semanticFamilyCount: roleFamilies[role].length,
      datasetSha256: sha256Hex(toJsonl(rows)),
      taskManifestPath: manifests[role]?.path || null,
    }])),
    referenceQualification: {
      taskManifestPath: stablePath(repoRoot, qualificationPath),
      taskCount: qualificationTasks.length,
      trainingFamilyRepresentatives: trainingRepresentatives.length,
    },
    isolation: {
      splitKey: 'semanticFamilyId',
      semanticFamilyOverlaps: overlaps,
      duplicateRowIds: allRows.length - rowIds.size,
      duplicatePrompts: allRows.length - promptHashes.size,
      mechanicsOracleExclusions: catalog.excludedOracleIds,
      visibleMechanicsPopulationUsedForTraining: false,
    },
    promotion: {
      status: 'external_custody_required',
      rows: 0,
      reason: 'A sealed one-use promotion population cannot be authored and inspected by the training operator.',
    },
    fileBindings,
    corpusSha256: sha256Hex(JSON.stringify(allRows)),
    claimBoundary: 'This corpus can train and evaluate complete 1-D elementwise f32 WGSL shaders under explicit interface contracts. It cannot establish arbitrary WGSL program synthesis, binding design, reductions, shared memory, atomics, textures, graphics stages, or deployment readiness.',
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

export async function writeWgslWriterCorpus(materialized) {
  for (const [filePath, contents] of materialized.files) {
    await mkdir(dirname(filePath), { recursive: true });
    await writeFile(filePath, contents, 'utf8');
  }
}

export async function checkWgslWriterCorpus(materialized) {
  const mismatches = [];
  for (const [filePath, expected] of materialized.files) {
    let actual = null;
    try {
      actual = await readFile(filePath, 'utf8');
    } catch {
      mismatches.push(`${stablePath(resolve('.'), filePath)}:missing`);
      continue;
    }
    if (actual !== expected) mismatches.push(`${stablePath(resolve('.'), filePath)}:drift`);
  }
  if (mismatches.length > 0) {
    throw new Error(`WGSL writer corpus drift:\n${mismatches.join('\n')}`);
  }
  return { checkedFiles: materialized.files.size };
}
