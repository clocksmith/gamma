import { readFile } from 'node:fs/promises';
import { isAbsolute, join, normalize, relative, resolve, sep } from 'node:path';

import { sha256Hex } from '../../src/utils/sha256.js';

export const HOST_TEACHER_LANES = Object.freeze(['javascript', 'wgsl']);
export const HOST_TEACHER_SPLITS = Object.freeze(['qualification', 'label', 'student_holdout']);
export const HOST_TEACHER_PROVIDERS = Object.freeze(['claude', 'codex']);

const PLACEHOLDER_PATTERN = /\{([a-zA-Z][a-zA-Z0-9]*)\}/g;
const ALLOWED_PROVIDER_PLACEHOLDERS = new Set([
  'modelId',
  'outputPath',
  'prompt',
  'schemaJson',
  'schemaPath',
  'workspace',
]);

function isObjectRecord(value) {
  return value != null && typeof value === 'object' && !Array.isArray(value);
}

function requireObject(value, label) {
  if (!isObjectRecord(value)) {
    throw new Error(`${label} must be an object.`);
  }
  return value;
}

function requireString(value, label) {
  if (typeof value !== 'string' || !value.trim()) {
    throw new Error(`${label} must be a non-empty string.`);
  }
  return value.trim();
}

function requireBoolean(value, label) {
  if (typeof value !== 'boolean') {
    throw new Error(`${label} must be a boolean.`);
  }
  return value;
}

function requireNumber(value, label, options = {}) {
  if (!Number.isFinite(value)) {
    throw new Error(`${label} must be finite.`);
  }
  if (options.integer === true && !Number.isInteger(value)) {
    throw new Error(`${label} must be an integer.`);
  }
  if (options.min !== undefined && value < options.min) {
    throw new Error(`${label} must be >= ${options.min}.`);
  }
  if (options.max !== undefined && value > options.max) {
    throw new Error(`${label} must be <= ${options.max}.`);
  }
  return value;
}

function requireStringArray(value, label, options = {}) {
  if (!Array.isArray(value)) {
    throw new Error(`${label} must be an array.`);
  }
  if (options.minItems !== undefined && value.length < options.minItems) {
    throw new Error(`${label} must contain at least ${options.minItems} entries.`);
  }
  const normalized = value.map((entry, index) => requireString(entry, `${label}[${index}]`));
  if (new Set(normalized).size !== normalized.length) {
    throw new Error(`${label} must not contain duplicates.`);
  }
  return normalized;
}

export function normalizeRepoRelativePath(value, label = 'path') {
  const text = requireString(value, label);
  if (isAbsolute(text) || text.includes('\\')) {
    throw new Error(`${label} must be a repo-relative POSIX path.`);
  }
  const segments = text.split('/');
  if (segments.includes('..') || segments.includes('.')) {
    throw new Error(`${label} must not contain dot segments.`);
  }
  const normalizedPath = normalize(text).split(sep).join('/');
  if (!normalizedPath || normalizedPath.startsWith('../')) {
    throw new Error(`${label} must stay inside the repository.`);
  }
  return normalizedPath;
}

function normalizeRepoRelativePaths(value, label, options = {}) {
  return requireStringArray(value, label, options)
    .map((entry, index) => normalizeRepoRelativePath(entry, `${label}[${index}]`));
}

function assertKnownKeys(value, allowed, label) {
  for (const key of Object.keys(value)) {
    if (!allowed.has(key)) {
      throw new Error(`${label}.${key} is not supported.`);
    }
  }
}

function validateProviderTemplateArg(value, label) {
  const text = requireString(value, label);
  for (const match of text.matchAll(PLACEHOLDER_PATTERN)) {
    if (!ALLOWED_PROVIDER_PLACEHOLDERS.has(match[1])) {
      throw new Error(`${label} uses unsupported placeholder {${match[1]}}.`);
    }
  }
  return text;
}

function validateProvider(providerId, value) {
  const provider = requireObject(value, `host teacher policy providers.${providerId}`);
  assertKnownKeys(provider, new Set([
    'command',
    'versionArgs',
    'modelEnvironmentVariable',
    'promptTransport',
    'args',
    'eventFormat',
    'finalOutputMode',
  ]), `host teacher policy providers.${providerId}`);
  const promptTransport = requireString(provider.promptTransport, `providers.${providerId}.promptTransport`);
  if (!['argument', 'stdin'].includes(promptTransport)) {
    throw new Error(`providers.${providerId}.promptTransport must be "argument" or "stdin".`);
  }
  const eventFormat = requireString(provider.eventFormat, `providers.${providerId}.eventFormat`);
  if (eventFormat !== 'jsonl') {
    throw new Error(`providers.${providerId}.eventFormat must be "jsonl".`);
  }
  const finalOutputMode = requireString(provider.finalOutputMode, `providers.${providerId}.finalOutputMode`);
  if (!['jsonl_result', 'file'].includes(finalOutputMode)) {
    throw new Error(`providers.${providerId}.finalOutputMode must be "jsonl_result" or "file".`);
  }
  return {
    command: requireString(provider.command, `providers.${providerId}.command`),
    versionArgs: requireStringArray(provider.versionArgs, `providers.${providerId}.versionArgs`),
    modelEnvironmentVariable: requireString(
      provider.modelEnvironmentVariable,
      `providers.${providerId}.modelEnvironmentVariable`
    ),
    promptTransport,
    args: requireStringArray(provider.args, `providers.${providerId}.args`, { minItems: 1 })
      .map((entry, index) => validateProviderTemplateArg(entry, `providers.${providerId}.args[${index}]`)),
    eventFormat,
    finalOutputMode,
  };
}

function validateCommand(value, label) {
  const command = requireObject(value, label);
  assertKnownKeys(command, new Set(['id', 'command', 'args']), label);
  return {
    id: requireString(command.id, `${label}.id`),
    command: requireString(command.command, `${label}.command`),
    args: requireStringArray(command.args, `${label}.args`),
  };
}

function validateMutation(value, label) {
  const mutation = requireObject(value, label);
  assertKnownKeys(mutation, new Set(['path', 'find', 'replace', 'occurrences']), label);
  const find = requireString(mutation.find, `${label}.find`);
  if (typeof mutation.replace !== 'string') {
    throw new Error(`${label}.replace must be a string.`);
  }
  if (find === mutation.replace) {
    throw new Error(`${label}.replace must differ from find.`);
  }
  return {
    path: normalizeRepoRelativePath(mutation.path, `${label}.path`),
    find,
    replace: mutation.replace,
    occurrences: requireNumber(mutation.occurrences, `${label}.occurrences`, {
      integer: true,
      min: 1,
    }),
  };
}

function validateTask(value, index) {
  const label = `host teacher task bank tasks[${index}]`;
  const task = requireObject(value, label);
  assertKnownKeys(task, new Set([
    'id',
    'lane',
    'split',
    'title',
    'prompt',
    'sourceFiles',
    'allowedChangedPaths',
    'mutations',
    'validationCommands',
  ]), label);
  const lane = requireString(task.lane, `${label}.lane`);
  if (!HOST_TEACHER_LANES.includes(lane)) {
    throw new Error(`${label}.lane must be one of ${HOST_TEACHER_LANES.join(', ')}.`);
  }
  const split = requireString(task.split, `${label}.split`);
  if (!HOST_TEACHER_SPLITS.includes(split)) {
    throw new Error(`${label}.split must be one of ${HOST_TEACHER_SPLITS.join(', ')}.`);
  }
  const sourceFiles = normalizeRepoRelativePaths(task.sourceFiles, `${label}.sourceFiles`, { minItems: 1 });
  const allowedChangedPaths = normalizeRepoRelativePaths(
    task.allowedChangedPaths,
    `${label}.allowedChangedPaths`,
    { minItems: 1 }
  );
  const mutations = Array.isArray(task.mutations)
    ? task.mutations.map((entry, mutationIndex) => validateMutation(entry, `${label}.mutations[${mutationIndex}]`))
    : null;
  if (!mutations || mutations.length === 0) {
    throw new Error(`${label}.mutations must contain at least one mutation.`);
  }
  for (const mutation of mutations) {
    if (!allowedChangedPaths.includes(mutation.path)) {
      throw new Error(`${label}: mutation path ${mutation.path} must be allowed to change.`);
    }
    if (!sourceFiles.includes(mutation.path)) {
      throw new Error(`${label}: mutation path ${mutation.path} must appear in sourceFiles.`);
    }
  }
  const validationCommands = Array.isArray(task.validationCommands)
    ? task.validationCommands.map((entry, commandIndex) => validateCommand(
      entry,
      `${label}.validationCommands[${commandIndex}]`
    ))
    : null;
  if (!validationCommands || validationCommands.length === 0) {
    throw new Error(`${label}.validationCommands must contain at least one command.`);
  }
  return {
    id: requireString(task.id, `${label}.id`),
    lane,
    split,
    title: requireString(task.title, `${label}.title`),
    prompt: requireString(task.prompt, `${label}.prompt`),
    sourceFiles,
    allowedChangedPaths,
    mutations,
    validationCommands,
  };
}

export function validateHostTeacherTaskBank(value) {
  const bank = requireObject(value, 'host teacher task bank');
  assertKnownKeys(bank, new Set([
    '$schema',
    'schemaVersion',
    'source',
    'bankId',
    'baseRevision',
    'studentBaseModelId',
    'tasks',
  ]), 'host teacher task bank');
  if (bank.schemaVersion !== 1) {
    throw new Error('host teacher task bank schemaVersion must be 1.');
  }
  if (bank.source !== 'doppler') {
    throw new Error('host teacher task bank source must be "doppler".');
  }
  const tasks = Array.isArray(bank.tasks)
    ? bank.tasks.map((task, index) => validateTask(task, index))
    : null;
  if (!tasks || tasks.length === 0) {
    throw new Error('host teacher task bank tasks must contain at least one task.');
  }
  const ids = tasks.map((task) => task.id);
  if (new Set(ids).size !== ids.length) {
    throw new Error('host teacher task bank task ids must be unique.');
  }
  for (const lane of HOST_TEACHER_LANES) {
    for (const split of HOST_TEACHER_SPLITS) {
      if (!tasks.some((task) => task.lane === lane && task.split === split)) {
        throw new Error(`host teacher task bank requires at least one ${lane}/${split} task.`);
      }
    }
  }
  return {
    schemaVersion: 1,
    source: 'doppler',
    bankId: requireString(bank.bankId, 'host teacher task bank bankId'),
    baseRevision: requireString(bank.baseRevision, 'host teacher task bank baseRevision'),
    studentBaseModelId: requireString(
      bank.studentBaseModelId,
      'host teacher task bank studentBaseModelId'
    ),
    tasks,
  };
}

export function validateHostTeacherPolicy(value) {
  const policy = requireObject(value, 'host teacher qualification policy');
  assertKnownKeys(policy, new Set([
    '$schema',
    'schemaVersion',
    'source',
    'policyId',
    'taskBankPath',
    'outputSchemaPath',
    'receiptSchemaPath',
    'harnessFiles',
    'snapshot',
    'providers',
    'evaluation',
  ]), 'host teacher qualification policy');
  if (policy.schemaVersion !== 1) {
    throw new Error('host teacher qualification policy schemaVersion must be 1.');
  }
  if (policy.source !== 'doppler') {
    throw new Error('host teacher qualification policy source must be "doppler".');
  }
  const snapshot = requireObject(policy.snapshot, 'host teacher qualification policy snapshot');
  assertKnownKeys(snapshot, new Set(['excludedPaths', 'linkNodeModules']), 'snapshot');
  const providers = requireObject(policy.providers, 'host teacher qualification policy providers');
  assertKnownKeys(providers, new Set(HOST_TEACHER_PROVIDERS), 'providers');
  const normalizedProviders = Object.fromEntries(HOST_TEACHER_PROVIDERS.map((providerId) => [
    providerId,
    validateProvider(providerId, providers[providerId]),
  ]));
  const evaluation = requireObject(policy.evaluation, 'host teacher qualification policy evaluation');
  assertKnownKeys(evaluation, new Set([
    'minPassRateByLane',
    'maxPolicyViolations',
    'forbiddenChangedPathPrefixes',
    'forbiddenCommandPatterns',
    'providerTieBreakOrder',
    'requireExactSourceRecovery',
  ]), 'evaluation');
  const minPassRateByLane = requireObject(evaluation.minPassRateByLane, 'evaluation.minPassRateByLane');
  assertKnownKeys(minPassRateByLane, new Set(HOST_TEACHER_LANES), 'evaluation.minPassRateByLane');
  const providerTieBreakOrder = requireStringArray(
    evaluation.providerTieBreakOrder,
    'evaluation.providerTieBreakOrder',
    { minItems: HOST_TEACHER_PROVIDERS.length }
  );
  if (
    providerTieBreakOrder.length !== HOST_TEACHER_PROVIDERS.length
    || providerTieBreakOrder.some((providerId) => !HOST_TEACHER_PROVIDERS.includes(providerId))
  ) {
    throw new Error('evaluation.providerTieBreakOrder must contain claude and codex exactly once.');
  }
  return {
    schemaVersion: 1,
    source: 'doppler',
    policyId: requireString(policy.policyId, 'host teacher qualification policy policyId'),
    taskBankPath: normalizeRepoRelativePath(policy.taskBankPath, 'policy.taskBankPath'),
    outputSchemaPath: normalizeRepoRelativePath(policy.outputSchemaPath, 'policy.outputSchemaPath'),
    receiptSchemaPath: normalizeRepoRelativePath(
      policy.receiptSchemaPath,
      'policy.receiptSchemaPath'
    ),
    harnessFiles: normalizeRepoRelativePaths(
      policy.harnessFiles,
      'policy.harnessFiles',
      { minItems: 1 }
    ),
    snapshot: {
      excludedPaths: normalizeRepoRelativePaths(snapshot.excludedPaths, 'snapshot.excludedPaths'),
      linkNodeModules: requireBoolean(snapshot.linkNodeModules, 'snapshot.linkNodeModules'),
    },
    providers: normalizedProviders,
    evaluation: {
      minPassRateByLane: Object.fromEntries(HOST_TEACHER_LANES.map((lane) => [
        lane,
        requireNumber(minPassRateByLane[lane], `evaluation.minPassRateByLane.${lane}`, {
          min: 0,
          max: 1,
        }),
      ])),
      maxPolicyViolations: requireNumber(
        evaluation.maxPolicyViolations,
        'evaluation.maxPolicyViolations',
        { integer: true, min: 0 }
      ),
      forbiddenChangedPathPrefixes: normalizeRepoRelativePaths(
        evaluation.forbiddenChangedPathPrefixes,
        'evaluation.forbiddenChangedPathPrefixes'
      ),
      forbiddenCommandPatterns: requireStringArray(
        evaluation.forbiddenCommandPatterns,
        'evaluation.forbiddenCommandPatterns'
      ),
      providerTieBreakOrder,
      requireExactSourceRecovery: requireBoolean(
        evaluation.requireExactSourceRecovery,
        'evaluation.requireExactSourceRecovery'
      ),
    },
  };
}

export function validateTeacherFinalOutput(value, task) {
  const output = requireObject(value, 'host teacher final output');
  assertKnownKeys(output, new Set([
    'taskId',
    'summary',
    'changedFiles',
    'verification',
    'residualRisks',
  ]), 'host teacher final output');
  const taskId = requireString(output.taskId, 'host teacher final output taskId');
  if (taskId !== task.id) {
    throw new Error(`host teacher final output taskId must be "${task.id}".`);
  }
  const changedFiles = normalizeRepoRelativePaths(
    output.changedFiles,
    'host teacher final output changedFiles',
    { minItems: 1 }
  );
  const verification = requireStringArray(
    output.verification,
    'host teacher final output verification',
    { minItems: 1 }
  );
  const residualRisks = requireStringArray(
    output.residualRisks,
    'host teacher final output residualRisks'
  );
  return {
    taskId,
    summary: requireString(output.summary, 'host teacher final output summary'),
    changedFiles,
    verification,
    residualRisks,
  };
}

async function readJsonArtifact(root, relativePath, label) {
  const absolutePath = resolve(root, relativePath);
  const relativeCheck = relative(root, absolutePath);
  if (relativeCheck.startsWith('..') || isAbsolute(relativeCheck)) {
    throw new Error(`${label} escapes the repository root.`);
  }
  const raw = await readFile(absolutePath, 'utf8');
  return {
    absolutePath,
    relativePath,
    raw,
    hash: sha256Hex(raw),
    value: JSON.parse(raw),
  };
}

export async function loadHostTeacherContracts(options = {}) {
  const root = resolve(options.root || process.cwd());
  const policyPath = normalizeRepoRelativePath(
    options.policyPath || 'tools/policies/host-teacher-qualification-policy.json',
    'policy path'
  );
  const policyArtifact = await readJsonArtifact(root, policyPath, 'host teacher policy');
  const policy = validateHostTeacherPolicy(policyArtifact.value);
  const taskBankPath = normalizeRepoRelativePath(
    options.taskBankPath || policy.taskBankPath,
    'task bank path'
  );
  const taskBankArtifact = await readJsonArtifact(root, taskBankPath, 'host teacher task bank');
  const taskBank = validateHostTeacherTaskBank(taskBankArtifact.value);
  const outputSchemaArtifact = await readJsonArtifact(
    root,
    policy.outputSchemaPath,
    'host teacher output schema'
  );
  const receiptSchemaArtifact = await readJsonArtifact(
    root,
    policy.receiptSchemaPath,
    'host teacher receipt schema'
  );
  const harnessFiles = await Promise.all(policy.harnessFiles.map(async (relativePath) => {
    const absolutePath = resolve(root, relativePath);
    const content = await readFile(absolutePath, 'utf8');
    return {
      path: relativePath,
      hash: sha256Hex(content),
    };
  }));
  const harnessHash = sha256Hex(
    harnessFiles.map((file) => `${file.path}\0${file.hash}\n`).join('')
  );
  return {
    root,
    policy,
    policyArtifact,
    taskBank,
    taskBankArtifact,
    outputSchema: outputSchemaArtifact.value,
    outputSchemaArtifact,
    receiptSchema: receiptSchemaArtifact.value,
    receiptSchemaArtifact,
    harnessFiles,
    harnessHash,
  };
}

export function selectHostTeacherTasks(taskBank, options = {}) {
  const lanes = options.lanes?.length ? options.lanes : HOST_TEACHER_LANES;
  const splits = options.splits?.length ? options.splits : ['qualification'];
  const taskIds = options.taskIds?.length ? new Set(options.taskIds) : null;
  for (const lane of lanes) {
    if (!HOST_TEACHER_LANES.includes(lane)) {
      throw new Error(`Unknown host teacher lane "${lane}".`);
    }
  }
  for (const split of splits) {
    if (!HOST_TEACHER_SPLITS.includes(split)) {
      throw new Error(`Unknown host teacher split "${split}".`);
    }
  }
  const selected = taskBank.tasks.filter((task) => (
    lanes.includes(task.lane)
    && splits.includes(task.split)
    && (!taskIds || taskIds.has(task.id))
  ));
  if (taskIds) {
    const found = new Set(selected.map((task) => task.id));
    const missing = [...taskIds].filter((taskId) => !found.has(taskId));
    if (missing.length > 0) {
      throw new Error(`Unknown or filtered host teacher task ids: ${missing.join(', ')}.`);
    }
  }
  if (selected.length === 0) {
    throw new Error('Host teacher task selection is empty.');
  }
  return selected;
}

export function renderProviderArgs(provider, values) {
  return provider.args.map((arg) => arg.replace(PLACEHOLDER_PATTERN, (_match, key) => {
    if (!Object.hasOwn(values, key)) {
      throw new Error(`Missing provider argument placeholder value for {${key}}.`);
    }
    return String(values[key]);
  }));
}

export function resolveRepoPath(root, relativePath) {
  return join(resolve(root), normalizeRepoRelativePath(relativePath));
}
