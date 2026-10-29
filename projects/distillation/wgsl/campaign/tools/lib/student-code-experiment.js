import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { dirname, join, relative, resolve } from 'node:path';

import { formatChatMessages } from '../../src/inference/pipelines/text/chat-format.js';
import { sha256Hex } from '../../src/utils/sha256.js';
import {
  HOST_TEACHER_LANES,
  loadHostTeacherContracts,
  normalizeRepoRelativePath,
  selectHostTeacherTasks,
} from './host-teacher-contracts.js';
import { runHostProcess } from './host-teacher-process.js';
import {
  createHostTeacherWorkspace,
  readWorkspacePatch,
  readWorkspaceStatus,
} from './host-teacher-workspace.js';

export const DEFAULT_STUDENT_CODE_POLICY_PATH =
  'tools/policies/student-code-experiment-policy.json';

const STUDENT_VARIANTS = Object.freeze(['baseline', 'javascript', 'wgsl', 'mixed']);
const REQUIRED_ADAPTERS = Object.freeze(['javascript', 'wgsl', 'mixed']);
const FAILURE_SAFE_FIELDS = Object.freeze([
  'artifactType',
  'schemaVersion',
  'source',
  'experimentId',
  'variant',
  'lane',
  'sourceTaskFingerprint',
  'failureCodes',
  'observations',
  'outputHashes',
  'nextLabelRound',
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
  if (options.min != null && value < options.min) {
    throw new Error(`${label} must be >= ${options.min}.`);
  }
  if (options.max != null && value > options.max) {
    throw new Error(`${label} must be <= ${options.max}.`);
  }
  return value;
}

function requireStringArray(value, label, options = {}) {
  if (!Array.isArray(value)) {
    throw new Error(`${label} must be an array.`);
  }
  if (options.minItems != null && value.length < options.minItems) {
    throw new Error(`${label} must contain at least ${options.minItems} entries.`);
  }
  const rows = value.map((entry, index) => requireString(entry, `${label}[${index}]`));
  if (new Set(rows).size !== rows.length) {
    throw new Error(`${label} must not contain duplicates.`);
  }
  return rows;
}

function requireExactKeys(value, allowedKeys, label) {
  const observed = Object.keys(value).sort((left, right) => left.localeCompare(right));
  const expected = [...allowedKeys].sort((left, right) => left.localeCompare(right));
  if (
    observed.length !== expected.length
    || observed.some((key, index) => key !== expected[index])
  ) {
    throw new Error(`${label} must contain exactly: ${expected.join(', ')}.`);
  }
}

function validateAdapter(value, index) {
  const label = `student code policy adapters[${index}]`;
  const adapter = requireObject(value, label);
  const id = requireString(adapter.id, `${label}.id`);
  if (!REQUIRED_ADAPTERS.includes(id)) {
    throw new Error(`${label}.id must be one of ${REQUIRED_ADAPTERS.join(', ')}.`);
  }
  const lanes = requireStringArray(adapter.lanes, `${label}.lanes`, { minItems: 1 });
  if (lanes.some((lane) => !HOST_TEACHER_LANES.includes(lane))) {
    throw new Error(`${label}.lanes contains an unknown lane.`);
  }
  return {
    id,
    lanes,
    balanceLanes: adapter.balanceLanes === true,
  };
}

export function validateStudentCodePolicy(value) {
  const policy = requireObject(value, 'student code policy');
  if (policy.schemaVersion !== 1) {
    throw new Error('student code policy schemaVersion must be 1.');
  }
  if (policy.source !== 'doppler') {
    throw new Error('student code policy source must be "doppler".');
  }
  const baseModel = requireObject(policy.baseModel, 'student code policy baseModel');
  const prompt = requireObject(policy.prompt, 'student code policy prompt');
  const generation = requireObject(policy.generation, 'student code policy generation');
  const training = requireObject(policy.training, 'student code policy training');
  const promotion = requireObject(policy.promotion, 'student code policy promotion');
  const adapters = Array.isArray(policy.adapters)
    ? policy.adapters.map((adapter, index) => validateAdapter(adapter, index))
    : null;
  if (!adapters || adapters.length !== REQUIRED_ADAPTERS.length) {
    throw new Error(`student code policy requires ${REQUIRED_ADAPTERS.length} adapters.`);
  }
  const adapterIds = adapters.map((adapter) => adapter.id);
  if (REQUIRED_ADAPTERS.some((id) => !adapterIds.includes(id))) {
    throw new Error(`student code policy adapters must include ${REQUIRED_ADAPTERS.join(', ')}.`);
  }
  const lanes = requireStringArray(policy.lanes, 'student code policy lanes', { minItems: 1 });
  if (
    lanes.length !== HOST_TEACHER_LANES.length
    || HOST_TEACHER_LANES.some((lane) => !lanes.includes(lane))
  ) {
    throw new Error(`student code policy lanes must contain ${HOST_TEACHER_LANES.join(', ')}.`);
  }
  const requiredWinningLanes = requireStringArray(
    promotion.requiredWinningLanes,
    'student code policy promotion.requiredWinningLanes',
    { minItems: 1 }
  );
  const repetitions = requireNumber(
    generation.repetitions,
    'student code policy generation.repetitions',
    { integer: true, min: 2 }
  );
  const requiredRepetitions = requireNumber(
    promotion.requiredRepetitions,
    'student code policy promotion.requiredRepetitions',
    { integer: true, min: 2 }
  );
  if (requiredRepetitions !== repetitions) {
    throw new Error('student code policy promotion repetitions must match generation repetitions.');
  }
  const challengers = Array.isArray(policy.challengers)
    ? policy.challengers.map((entry, index) => {
      const challenger = requireObject(entry, `student code policy challengers[${index}]`);
      return {
        id: requireString(challenger.id, `challengers[${index}].id`),
        family: requireString(challenger.family, `challengers[${index}].family`),
        status: requireString(challenger.status, `challengers[${index}].status`),
        trainer: requireString(challenger.trainer, `challengers[${index}].trainer`),
      };
    })
    : null;
  if (!challengers || challengers.length < 2) {
    throw new Error('student code policy requires Qwen and Gemma challenger entries.');
  }
  if (!challengers.some((entry) => entry.family === 'qwen3')) {
    throw new Error('student code policy requires a qwen3 challenger.');
  }
  if (!challengers.some((entry) => entry.family === 'gemma4')) {
    throw new Error('student code policy requires a gemma4 challenger.');
  }

  return {
    schemaVersion: 1,
    source: 'doppler',
    policyId: requireString(policy.policyId, 'student code policy policyId'),
    releaseTarget: requireString(policy.releaseTarget, 'student code policy releaseTarget'),
    claimBoundary: requireString(policy.claimBoundary, 'student code policy claimBoundary'),
    taskBankPath: normalizeRepoRelativePath(
      policy.taskBankPath,
      'student code policy taskBankPath'
    ),
    harnessFiles: requireStringArray(
      policy.harnessFiles,
      'student code policy harnessFiles',
      { minItems: 1 }
    ).map((path, index) => normalizeRepoRelativePath(
      path,
      `student code policy harnessFiles[${index}]`
    )),
    baseModel: {
      id: requireString(baseModel.id, 'student code policy baseModel.id'),
      modelRef: requireString(baseModel.modelRef, 'student code policy baseModel.modelRef'),
      chatTemplate: requireString(
        baseModel.chatTemplate,
        'student code policy baseModel.chatTemplate'
      ),
    },
    lanes,
    holdoutSplit: requireString(policy.holdoutSplit, 'student code policy holdoutSplit'),
    prompt: {
      contextLines: requireNumber(prompt.contextLines, 'student code policy prompt.contextLines', {
        integer: true,
        min: 0,
      }),
      maxSourceChars: requireNumber(
        prompt.maxSourceChars,
        'student code policy prompt.maxSourceChars',
        { integer: true, min: 1 }
      ),
    },
    generation: {
      repetitions,
      seed: requireNumber(generation.seed, 'student code policy generation.seed', {
        integer: true,
      }),
      maxTokens: requireNumber(generation.maxTokens, 'student code policy generation.maxTokens', {
        integer: true,
        min: 1,
      }),
      temperature: requireNumber(
        generation.temperature,
        'student code policy generation.temperature',
        { min: 0 }
      ),
      topK: requireNumber(generation.topK, 'student code policy generation.topK', {
        integer: true,
        min: 1,
      }),
      topP: requireNumber(generation.topP, 'student code policy generation.topP', {
        min: 0,
        max: 1,
      }),
      repetitionPenalty: requireNumber(
        generation.repetitionPenalty,
        'student code policy generation.repetitionPenalty',
        { min: 0 }
      ),
    },
    training: {
      datasetPasses: requireNumber(
        training.datasetPasses,
        'student code policy training.datasetPasses',
        { integer: true, min: 1 }
      ),
      maxLength: requireNumber(training.maxLength, 'student code policy training.maxLength', {
        integer: true,
        min: 2,
      }),
      learningRate: requireNumber(
        training.learningRate,
        'student code policy training.learningRate',
        { min: 0 }
      ),
      rank: requireNumber(training.rank, 'student code policy training.rank', {
        integer: true,
        min: 1,
      }),
      alpha: requireNumber(training.alpha, 'student code policy training.alpha', { min: 0 }),
      dropout: requireNumber(training.dropout, 'student code policy training.dropout', {
        min: 0,
        max: 1,
      }),
      targetModules: requireStringArray(
        training.targetModules,
        'student code policy training.targetModules',
        { minItems: 1 }
      ),
      gradientMaxNorm: requireNumber(
        training.gradientMaxNorm,
        'student code policy training.gradientMaxNorm',
        { min: 0 }
      ),
    },
    adapters,
    promotion: {
      requiredRepetitions,
      requireStrictPassRateImprovement: requireBoolean(
        promotion.requireStrictPassRateImprovement,
        'student code policy promotion.requireStrictPassRateImprovement'
      ),
      requireDeterministicOutputs: requireBoolean(
        promotion.requireDeterministicOutputs,
        'student code policy promotion.requireDeterministicOutputs'
      ),
      maxPolicyViolations: requireNumber(
        promotion.maxPolicyViolations,
        'student code policy promotion.maxPolicyViolations',
        { integer: true, min: 0 }
      ),
      requiredWinningLanes,
    },
    challengers,
  };
}

export async function loadStudentCodeExperimentContracts(options = {}) {
  const root = resolve(options.root || process.cwd());
  const policyPath = normalizeRepoRelativePath(
    options.policyPath || DEFAULT_STUDENT_CODE_POLICY_PATH,
    'student code policy path'
  );
  const absolutePolicyPath = resolve(root, policyPath);
  const policyRaw = await readFile(absolutePolicyPath, 'utf8');
  const policy = validateStudentCodePolicy(JSON.parse(policyRaw));
  const harnessFiles = await Promise.all(policy.harnessFiles.map(async (path) => {
    const content = await readFile(resolve(root, path), 'utf8');
    return {
      path,
      hash: sha256Hex(content),
    };
  }));
  const harnessHash = sha256Hex(
    harnessFiles.map((file) => `${file.path}\0${file.hash}\n`).join('')
  );
  const host = await loadHostTeacherContracts({
    root,
    taskBankPath: policy.taskBankPath,
  });
  if (host.taskBankArtifact.relativePath !== policy.taskBankPath) {
    throw new Error('student code policy task bank did not resolve to the requested path.');
  }
  return {
    root,
    policyPath,
    absolutePolicyPath,
    policyRaw,
    policyHash: sha256Hex(policyRaw),
    policy,
    harnessFiles,
    harnessHash,
    host,
  };
}

function countOccurrences(source, needle) {
  let count = 0;
  let offset = 0;
  while (offset <= source.length - needle.length) {
    const found = source.indexOf(needle, offset);
    if (found === -1) break;
    count += 1;
    offset = found + needle.length;
  }
  return count;
}

function findOccurrenceOffsets(source, needle) {
  const offsets = [];
  let offset = 0;
  while (offset <= source.length - needle.length) {
    const found = source.indexOf(needle, offset);
    if (found === -1) break;
    offsets.push(found);
    offset = found + needle.length;
  }
  return offsets;
}

function lineIndexAt(source, offset) {
  let line = 0;
  for (let index = 0; index < offset; index += 1) {
    if (source[index] === '\n') line += 1;
  }
  return line;
}

function mergeLineRanges(ranges) {
  const sorted = [...ranges].sort((left, right) => left.start - right.start || left.end - right.end);
  const merged = [];
  for (const range of sorted) {
    const previous = merged[merged.length - 1];
    if (previous && range.start <= previous.end + 1) {
      previous.end = Math.max(previous.end, range.end);
    } else {
      merged.push({ ...range });
    }
  }
  return merged;
}

async function renderMutatedSourceExcerpts(workspace, task, promptPolicy) {
  const excerpts = [];
  const mutationPaths = [...new Set(task.mutations.map((mutation) => mutation.path))];
  for (const path of mutationPaths) {
    // Source paths are pinned by the task bank and resolved inside the disposable snapshot.
    // eslint-disable-next-line no-await-in-loop
    const source = await readFile(resolve(workspace, path), 'utf8');
    const lines = source.split('\n');
    const ranges = [];
    for (const mutation of task.mutations.filter((entry) => entry.path === path)) {
      const offsets = findOccurrenceOffsets(source, mutation.replace);
      if (offsets.length !== mutation.occurrences) {
        throw new Error(
          `${task.id}: expected ${mutation.occurrences} defective occurrence(s) in ${path}, found ${offsets.length}.`
        );
      }
      for (const offset of offsets) {
        const firstLine = lineIndexAt(source, offset);
        const finalLine = firstLine + mutation.replace.split('\n').length - 1;
        ranges.push({
          start: Math.max(0, firstLine - promptPolicy.contextLines),
          end: Math.min(lines.length - 1, finalLine + promptPolicy.contextLines),
        });
      }
    }
    for (const range of mergeLineRanges(ranges)) {
      excerpts.push(
        `--- ${path} lines ${range.start + 1}-${range.end + 1} ---\n`
        + lines.slice(range.start, range.end + 1).join('\n')
      );
    }
  }
  const rendered = excerpts.join('\n');
  if (rendered.length > promptPolicy.maxSourceChars) {
    throw new Error(
      `${task.id}: rendered source excerpt has ${rendered.length} chars, exceeding ${promptPolicy.maxSourceChars}.`
    );
  }
  return rendered;
}

export async function renderStudentTaskPrompt(contracts, task, options = {}) {
  const workspaceState = await createHostTeacherWorkspace(contracts.host, task,
    options.keepWorkspace === true ? {} : { paths: [...new Set(task.mutations.map(mutation => mutation.path))] });
  try {
    const excerpts = await renderMutatedSourceExcerpts(
      workspaceState.workspace,
      task,
      contracts.policy.prompt
    );
    const allowedPaths = task.allowedChangedPaths.join(', ');
    return [
      'Repair one Doppler defect. Return one compact JSON object and nothing else.',
      'The object has only "edits". Each edit has only "path", "find", "replace", and positive integer "occurrences".',
      'Use exact current source text in "find". Do not use markdown or explanations.',
      `Defect: ${task.prompt}`,
      `Allowed paths: ${allowedPaths}`,
      'Current source:',
      excerpts,
    ].join('\n');
  } finally {
    if (options.keepWorkspace !== true) {
      await workspaceState.cleanup();
    }
  }
}

export function buildGoldStudentCandidate(task) {
  return {
    edits: task.mutations.map((mutation) => ({
      path: mutation.path,
      find: mutation.replace,
      replace: mutation.find,
      occurrences: mutation.occurrences,
    })),
  };
}

function extractCandidateJson(rawOutput) {
  const raw = String(rawOutput ?? '');
  const trimmed = raw.trim();
  if (!trimmed) {
    return { text: '', wrapper: null };
  }
  if (trimmed.startsWith('{') && trimmed.endsWith('}')) {
    return { text: trimmed, wrapper: null };
  }
  const fenced = trimmed.match(/^```(?:json)?\s*([\s\S]*?)\s*```$/i);
  if (fenced) {
    return { text: fenced[1].trim(), wrapper: 'markdown_fence' };
  }
  const start = trimmed.indexOf('{');
  const end = trimmed.lastIndexOf('}');
  if (start >= 0 && end > start) {
    return { text: trimmed.slice(start, end + 1), wrapper: 'surrounding_text' };
  }
  return { text: trimmed, wrapper: 'non_json_output' };
}

function addViolation(violations, code, detail) {
  violations.push({ code, detail });
}

export function parseStudentCandidateOutput(rawOutput) {
  const extracted = extractCandidateJson(rawOutput);
  const violations = [];
  if (extracted.wrapper) {
    addViolation(violations, 'output_wrapper', extracted.wrapper);
  }
  let parsed;
  try {
    parsed = JSON.parse(extracted.text);
  } catch (error) {
    addViolation(violations, 'invalid_json', error.message);
    return {
      candidate: null,
      schemaValid: false,
      jsonText: extracted.text,
      violations,
    };
  }
  if (!isObjectRecord(parsed)) {
    addViolation(violations, 'invalid_top_level', 'candidate must be an object');
    return {
      candidate: null,
      schemaValid: false,
      jsonText: extracted.text,
      violations,
    };
  }
  try {
    requireExactKeys(parsed, ['edits'], 'student candidate');
  } catch (error) {
    addViolation(violations, 'invalid_top_level_keys', error.message);
  }
  if (!Array.isArray(parsed.edits) || parsed.edits.length < 1 || parsed.edits.length > 8) {
    addViolation(violations, 'invalid_edits', 'edits must contain between 1 and 8 entries');
  }
  const edits = [];
  if (Array.isArray(parsed.edits)) {
    for (const [index, rawEdit] of parsed.edits.entries()) {
      if (!isObjectRecord(rawEdit)) {
        addViolation(violations, 'invalid_edit_record', `edits[${index}] must be an object`);
        continue;
      }
      try {
        requireExactKeys(
          rawEdit,
          ['path', 'find', 'replace', 'occurrences'],
          `student candidate edits[${index}]`
        );
      } catch (error) {
        addViolation(violations, 'invalid_edit_keys', error.message);
        continue;
      }
      let path;
      try {
        path = normalizeRepoRelativePath(rawEdit.path, `student candidate edits[${index}].path`);
      } catch (error) {
        addViolation(violations, 'invalid_edit_path', error.message);
        continue;
      }
      if (typeof rawEdit.find !== 'string' || rawEdit.find.length === 0) {
        addViolation(violations, 'invalid_edit_find', `edits[${index}].find must be non-empty`);
        continue;
      }
      if (typeof rawEdit.replace !== 'string') {
        addViolation(violations, 'invalid_edit_replace', `edits[${index}].replace must be a string`);
        continue;
      }
      if (rawEdit.find === rawEdit.replace) {
        addViolation(violations, 'no_op_edit', `edits[${index}] does not change source`);
        continue;
      }
      if (!Number.isInteger(rawEdit.occurrences) || rawEdit.occurrences < 1) {
        addViolation(
          violations,
          'invalid_edit_occurrences',
          `edits[${index}].occurrences must be a positive integer`
        );
        continue;
      }
      edits.push({
        path,
        find: rawEdit.find,
        replace: rawEdit.replace,
        occurrences: rawEdit.occurrences,
      });
    }
  }
  const schemaViolationCodes = new Set([
    'invalid_json',
    'invalid_top_level',
    'invalid_top_level_keys',
    'invalid_edits',
    'invalid_edit_record',
    'invalid_edit_keys',
    'invalid_edit_path',
    'invalid_edit_find',
    'invalid_edit_replace',
    'no_op_edit',
    'invalid_edit_occurrences',
  ]);
  const schemaValid = edits.length > 0
    && !violations.some((violation) => schemaViolationCodes.has(violation.code));
  return {
    candidate: schemaValid ? { edits } : null,
    schemaValid,
    jsonText: extracted.text,
    violations,
  };
}

function sameStringSet(left, right) {
  if (left.length !== right.length) return false;
  const rightSet = new Set(right);
  return left.every((value) => rightSet.has(value));
}

async function runValidationCommands(workspace, commands) {
  const rows = [];
  for (const validation of commands) {
    // Task validators are ordered contract inputs and remain serialized.
    // eslint-disable-next-line no-await-in-loop
    const processResult = await runHostProcess(validation.command, validation.args, { cwd: workspace });
    rows.push({
      id: validation.id,
      command: validation.command,
      args: validation.args,
      code: processResult.code,
      signal: processResult.signal,
      stdoutHash: sha256Hex(processResult.stdout),
      stderrHash: sha256Hex(processResult.stderr),
      passed: processResult.code === 0 && !processResult.signal,
    });
  }
  return rows;
}

async function evaluateExactRecovery(workspaceState) {
  const rows = [];
  for (const [path, original] of workspaceState.originals) {
    try {
      // Recovery is checked against pinned original bytes, independent of model prose.
      // eslint-disable-next-line no-await-in-loop
      const content = await readFile(resolve(workspaceState.workspace, path), 'utf8');
      const observedHash = sha256Hex(content);
      rows.push({
        path,
        expectedHash: original.hash,
        mutatedHash: original.mutatedHash,
        observedHash,
        passed: observedHash === original.hash,
      });
    } catch (error) {
      rows.push({
        path,
        expectedHash: original.hash,
        mutatedHash: original.mutatedHash,
        observedHash: null,
        passed: false,
        error: error.message,
      });
    }
  }
  return rows;
}

export async function evaluateStudentCandidate(options) {
  const {
    contracts,
    task,
    rawOutput,
    variant = 'baseline',
    repetition = 1,
    prompt = null,
  } = options;
  if (!STUDENT_VARIANTS.includes(variant)) {
    throw new Error(`Unknown student variant "${variant}".`);
  }
  const parsed = parseStudentCandidateOutput(rawOutput);
  const workspaceState = await createHostTeacherWorkspace(contracts.host, task);
  try {
    const policyViolations = [...parsed.violations];
    const applyErrors = [];
    if (parsed.schemaValid) {
      for (const edit of parsed.candidate.edits) {
        if (!task.allowedChangedPaths.includes(edit.path)) {
          addViolation(policyViolations, 'unauthorized_path', edit.path);
        }
      }
      if (!policyViolations.some((violation) => violation.code === 'unauthorized_path')) {
        for (const [index, edit] of parsed.candidate.edits.entries()) {
          try {
            const absolutePath = resolve(workspaceState.workspace, edit.path);
            // Candidate edits are intentionally applied in declared order.
            // eslint-disable-next-line no-await-in-loop
            const source = await readFile(absolutePath, 'utf8');
            const observed = countOccurrences(source, edit.find);
            if (observed !== edit.occurrences) {
              applyErrors.push({
                code: 'occurrence_mismatch',
                editIndex: index,
                path: edit.path,
                expected: edit.occurrences,
                observed,
              });
              continue;
            }
            // eslint-disable-next-line no-await-in-loop
            await writeFile(absolutePath, source.split(edit.find).join(edit.replace), 'utf8');
          } catch (error) {
            applyErrors.push({
              code: 'edit_apply_error',
              editIndex: index,
              path: edit.path,
              error: error.message,
            });
          }
        }
      }
    }
    const actualChangedPaths = await readWorkspaceStatus(workspaceState.workspace);
    const patch = await readWorkspacePatch(workspaceState.workspace);
    const exactRecovery = await evaluateExactRecovery(workspaceState);
    const validationCommands = await runValidationCommands(
      workspaceState.workspace,
      task.validationCommands
    );
    const changedPathsMatch = sameStringSet(actualChangedPaths, task.allowedChangedPaths);
    if (!changedPathsMatch) {
      addViolation(
        policyViolations,
        'changed_paths_mismatch',
        `expected ${task.allowedChangedPaths.join(', ') || '(none)'}, observed ${actualChangedPaths.join(', ') || '(none)'}`
      );
    }
    const patchApplicable = parsed.schemaValid
      && applyErrors.length === 0
      && parsed.candidate.edits.length > 0;
    const exactSourceRecovery = exactRecovery.every((entry) => entry.passed);
    const validationPassed = validationCommands.every((entry) => entry.passed);
    const passed = patchApplicable
      && policyViolations.length === 0
      && changedPathsMatch
      && exactSourceRecovery
      && validationPassed
      && patch.trim().length > 0;
    return {
      artifactType: 'student_code_constructive_replay',
      schemaVersion: 1,
      source: 'doppler',
      experimentId: contracts.policy.policyId,
      policyHash: contracts.policyHash,
      harnessHash: contracts.harnessHash,
      harnessFiles: contracts.harnessFiles,
      hostHarnessHash: contracts.host.harnessHash,
      taskBankId: contracts.host.taskBank.bankId,
      taskBankHash: contracts.host.taskBankArtifact.hash,
      baseRevision: contracts.host.taskBank.baseRevision,
      baseModelId: contracts.policy.baseModel.id,
      variant,
      repetition,
      task: {
        id: task.id,
        lane: task.lane,
        split: task.split,
      },
      promptHash: prompt == null ? null : sha256Hex(prompt),
      outputHash: sha256Hex(String(rawOutput ?? '')),
      parsedCandidateHash: parsed.candidate == null
        ? null
        : sha256Hex(JSON.stringify(parsed.candidate)),
      passed,
      checks: {
        jsonParsed: !parsed.violations.some((violation) => violation.code === 'invalid_json'),
        schemaValid: parsed.schemaValid,
        outputUnwrapped: !parsed.violations.some((violation) => violation.code === 'output_wrapper'),
        patchApplicable,
        changedPathsMatch,
        exactSourceRecovery,
        validationPassed,
      },
      policyViolationCount: policyViolations.length,
      policyViolations,
      applyErrors,
      actualChangedPaths,
      exactRecovery,
      validationCommands,
      patchHash: sha256Hex(patch),
      patchBytes: Buffer.byteLength(patch),
      patch,
    };
  } finally {
    await workspaceState.cleanup();
  }
}

function rate(numerator, denominator) {
  return denominator > 0 ? numerator / denominator : 0;
}

function summarizeReplayRows(rows) {
  const taskGroups = new Map();
  for (const row of rows) {
    const group = taskGroups.get(row.task.id) || [];
    group.push(row);
    taskGroups.set(row.task.id, group);
  }
  const deterministicTasks = [...taskGroups.values()].filter((group) => (
    new Set(group.map((row) => row.outputHash)).size === 1
  )).length;
  const passedRows = rows.filter((row) => row.passed).length;
  const applicableRows = rows.filter((row) => row.checks.patchApplicable).length;
  const validationRows = rows.filter((row) => row.checks.validationPassed).length;
  const generationDurationMs = rows.reduce(
    (sum, row) => sum + (Number.isFinite(row.performance?.generationDurationMs)
      ? row.performance.generationDurationMs
      : 0),
    0
  );
  const completionTokens = rows.reduce(
    (sum, row) => sum + (Number.isInteger(row.performance?.completionTokens)
      ? row.performance.completionTokens
      : 0),
    0
  );
  return {
    taskCount: taskGroups.size,
    replayCount: rows.length,
    passedReplays: passedRows,
    constructivePassRate: rate(passedRows, rows.length),
    applicableReplays: applicableRows,
    patchApplicabilityRate: rate(applicableRows, rows.length),
    validationPassedReplays: validationRows,
    validationPassRate: rate(validationRows, rows.length),
    policyViolationCount: rows.reduce((sum, row) => sum + row.policyViolationCount, 0),
    deterministicTasks,
    deterministicTaskRate: rate(deterministicTasks, taskGroups.size),
    deterministicOutputs: taskGroups.size > 0 && deterministicTasks === taskGroups.size,
    performance: {
      generationDurationMs,
      completionTokens,
      decodeTokensPerSecond: generationDurationMs > 0
        ? completionTokens / (generationDurationMs / 1000)
        : null,
    },
  };
}

export function buildStudentReplaySummary(variant, rows) {
  const selected = rows.filter((row) => row.variant === variant);
  const byLane = {};
  for (const lane of HOST_TEACHER_LANES) {
    byLane[lane] = summarizeReplayRows(selected.filter((row) => row.task.lane === lane));
  }
  return {
    artifactType: 'student_code_replay_summary',
    schemaVersion: 1,
    source: 'doppler',
    variant,
    overall: summarizeReplayRows(selected),
    byLane,
  };
}

function buildLaneComparison(policy, baselineLane, candidateLane) {
  const strictImprovement = candidateLane.constructivePassRate > baselineLane.constructivePassRate;
  const repetitionsPresent = candidateLane.replayCount
    === candidateLane.taskCount * policy.promotion.requiredRepetitions;
  const passRateRequirement = policy.promotion.requireStrictPassRateImprovement
    ? strictImprovement
    : candidateLane.constructivePassRate >= baselineLane.constructivePassRate;
  const deterministicRequirement = !policy.promotion.requireDeterministicOutputs
    || candidateLane.deterministicOutputs;
  const policyRequirement = candidateLane.policyViolationCount
    <= policy.promotion.maxPolicyViolations;
  return {
    baselinePassRate: baselineLane.constructivePassRate,
    candidatePassRate: candidateLane.constructivePassRate,
    absoluteImprovement:
      candidateLane.constructivePassRate - baselineLane.constructivePassRate,
    strictImprovement,
    repetitionsPresent,
    deterministicOutputs: candidateLane.deterministicOutputs,
    policyViolationCount: candidateLane.policyViolationCount,
    passed: passRateRequirement
      && repetitionsPresent
      && deterministicRequirement
      && policyRequirement,
  };
}

export function buildStudentPromotionReport(policy, summaries) {
  const baseline = summaries.baseline;
  if (!baseline) {
    throw new Error('student promotion report requires a baseline summary.');
  }
  const candidates = {};
  const candidateDefinitions = {
    specialized: {
      javascript: summaries.javascript?.byLane.javascript,
      wgsl: summaries.wgsl?.byLane.wgsl,
    },
    mixed: {
      javascript: summaries.mixed?.byLane.javascript,
      wgsl: summaries.mixed?.byLane.wgsl,
    },
  };
  for (const [candidateId, lanes] of Object.entries(candidateDefinitions)) {
    const laneResults = {};
    for (const lane of policy.promotion.requiredWinningLanes) {
      laneResults[lane] = lanes[lane]
        ? buildLaneComparison(policy, baseline.byLane[lane], lanes[lane])
        : {
          baselinePassRate: baseline.byLane[lane].constructivePassRate,
          candidatePassRate: null,
          absoluteImprovement: null,
          strictImprovement: false,
          repetitionsPresent: false,
          deterministicOutputs: false,
          policyViolationCount: null,
          passed: false,
        };
    }
    candidates[candidateId] = {
      laneResults,
      eligible: Object.values(laneResults).every((result) => result.passed),
    };
  }
  const controlProven = Object.values(candidates).some((candidate) => candidate.eligible);
  return {
    artifactType: 'student_code_promotion_report',
    schemaVersion: 1,
    source: 'doppler',
    policyId: policy.policyId,
    releaseTarget: policy.releaseTarget,
    claimBoundary: policy.claimBoundary,
    controlProven,
    evidenceClass: controlProven
      ? 'constructive_repeated_control_pass'
      : 'experimental_constructive_replay',
    candidates,
    challengers: policy.challengers.map((challenger) => ({
      ...challenger,
      status: controlProven ? 'eligible_for_external_trainer' : challenger.status,
    })),
  };
}

function failureCodesForRow(row) {
  const codes = row.policyViolations.map((violation) => violation.code);
  codes.push(...row.applyErrors.map((error) => error.code));
  if (!row.checks.patchApplicable) codes.push('patch_not_applicable');
  if (!row.checks.exactSourceRecovery) codes.push('exact_source_recovery_failed');
  if (!row.checks.validationPassed) codes.push('validation_failed');
  return [...new Set(codes)].sort((left, right) => left.localeCompare(right));
}

export function buildOuroborosFailureSignals(rows, experimentId) {
  const groups = new Map();
  for (const row of rows.filter((candidate) => !candidate.passed)) {
    const failureCodes = failureCodesForRow(row);
    const sourceTaskFingerprint = sha256Hex(row.task.id);
    const key = [
      row.variant,
      row.task.lane,
      sourceTaskFingerprint,
      failureCodes.join(','),
    ].join('\0');
    const group = groups.get(key) || {
      artifactType: 'student_code_ouroboros_failure_signal',
      schemaVersion: 1,
      source: 'doppler',
      experimentId,
      variant: row.variant,
      lane: row.task.lane,
      sourceTaskFingerprint,
      failureCodes,
      observations: 0,
      outputHashes: [],
      nextLabelRound: true,
    };
    group.observations += 1;
    if (!group.outputHashes.includes(row.outputHash)) group.outputHashes.push(row.outputHash);
    groups.set(key, group);
  }
  const signals = [...groups.values()].sort((left, right) => (
    left.variant.localeCompare(right.variant)
    || left.lane.localeCompare(right.lane)
    || left.sourceTaskFingerprint.localeCompare(right.sourceTaskFingerprint)
  ));
  for (const signal of signals) {
    requireExactKeys(signal, FAILURE_SAFE_FIELDS, 'Ouroboros failure signal');
  }
  return signals;
}

function assertAcceptedLabelReceipt(receipt, taskBankHash) {
  return receipt?.passed === true
    && receipt?.task?.split === 'label'
    && receipt?.taskBankHash === taskBankHash
    && receipt?.policyViolationCount === 0
    && receipt?.checks?.exactSourceRecovery === true
    && receipt?.checks?.validationCommandsPassed === true
    && receipt?.checks?.changedPathsAllowed === true;
}

async function readTeacherRun(teacherRunRoot) {
  const absoluteRoot = resolve(teacherRunRoot);
  const [contractRaw, receiptsRaw] = await Promise.all([
    readFile(join(absoluteRoot, 'run-contract.json'), 'utf8'),
    readFile(join(absoluteRoot, 'receipts.json'), 'utf8'),
  ]);
  const receipts = JSON.parse(receiptsRaw);
  if (!Array.isArray(receipts)) {
    throw new Error('teacher run receipts.json must be an array.');
  }
  return {
    root: absoluteRoot,
    runContract: JSON.parse(contractRaw),
    receipts,
    contractHash: sha256Hex(contractRaw),
    receiptsHash: sha256Hex(receiptsRaw),
  };
}

export async function buildStudentTrainingDatasets(options) {
  const { contracts, teacherRunRoot } = options;
  const teacherRun = await readTeacherRun(teacherRunRoot);
  if (teacherRun.runContract.taskBankHash !== contracts.host.taskBankArtifact.hash) {
    throw new Error(
      'teacher run task bank hash does not match the active student experiment task bank.'
    );
  }
  if (teacherRun.runContract.policyHash !== contracts.host.policyArtifact.hash) {
    throw new Error('teacher run policy hash does not match the active host teacher policy.');
  }
  const taskById = new Map(contracts.host.taskBank.tasks.map((task) => [task.id, task]));
  const eligibleAccepted = teacherRun.receipts
    .filter((receipt) => assertAcceptedLabelReceipt(
      receipt,
      contracts.host.taskBankArtifact.hash
    ))
    .sort((left, right) => left.task.id.localeCompare(right.task.id));
  const eligibleAcceptedLaneCounts = Object.fromEntries(contracts.policy.lanes.map((lane) => [
    lane,
    eligibleAccepted.filter((receipt) => receipt.task.lane === lane).length,
  ]));
  if (Math.min(...Object.values(eligibleAcceptedLaneCounts)) < 1) {
    throw new Error('teacher run does not contain an accepted label in every lane.');
  }
  const accepted = eligibleAccepted;
  const sourceRows = [];
  for (const receipt of accepted) {
    const task = taskById.get(receipt.task.id);
    if (!task || task.split !== 'label') {
      throw new Error(`accepted teacher receipt references unknown label task ${receipt.task.id}.`);
    }
    // Prompt materialization uses a fresh pinned mutation for every accepted label.
    // eslint-disable-next-line no-await-in-loop
    const taskPrompt = await renderStudentTaskPrompt(contracts, task);
    const prompt = formatChatMessages(
      [{ role: 'user', content: taskPrompt }],
      contracts.policy.baseModel.chatTemplate
    );
    const completion = `${JSON.stringify(buildGoldStudentCandidate(task))}<end_of_turn>\n`;
    sourceRows.push({
      id: `student-label-${receipt.sessionId}`,
      lane: task.lane,
      taskId: task.id,
      prompt,
      completion,
      teacherModelId: receipt.teacherModelId,
      teacherProvider: receipt.provider,
      qualificationReceipt: relative(
        contracts.root,
        join(teacherRun.root, 'sessions', receipt.sessionId, 'receipt.json')
      ).replaceAll('\\', '/'),
      promptHash: sha256Hex(taskPrompt),
      completionHash: sha256Hex(completion),
      taskBankHash: receipt.taskBankHash,
      policyHash: receipt.policyHash,
      evidenceClass: 'constructive_machine_replay',
    });
  }
  for (const lane of contracts.policy.lanes) {
    if (!sourceRows.some((row) => row.lane === lane)) {
      throw new Error(`teacher run exported no accepted ${lane} labels.`);
    }
  }
  const datasets = {};
  for (const adapter of contracts.policy.adapters) {
    let selected = sourceRows.filter((row) => adapter.lanes.includes(row.lane));
    if (adapter.balanceLanes && adapter.lanes.length > 1) {
      const countByLane = Object.fromEntries(adapter.lanes.map((lane) => [
        lane,
        selected.filter((row) => row.lane === lane).length,
      ]));
      const balancedCount = Math.min(...Object.values(countByLane));
      selected = adapter.lanes.flatMap((lane) => (
        selected.filter((row) => row.lane === lane).slice(0, balancedCount)
      ));
    }
    selected.sort((left, right) => left.id.localeCompare(right.id));
    const materializedRows = [];
    for (let pass = 1; pass <= contracts.policy.training.datasetPasses; pass += 1) {
      for (const row of selected) {
        materializedRows.push({
          ...row,
          id: `${row.id}--pass-${String(pass).padStart(2, '0')}`,
          datasetPass: pass,
        });
      }
    }
    datasets[adapter.id] = {
      adapter,
      sourceRowCount: selected.length,
      materializedRowCount: materializedRows.length,
      laneCounts: Object.fromEntries(contracts.policy.lanes.map((lane) => [
        lane,
        selected.filter((row) => row.lane === lane).length,
      ])),
      rows: materializedRows,
    };
  }
  return {
    artifactType: 'student_code_training_dataset_bundle',
    schemaVersion: 1,
    source: 'doppler',
    experimentId: contracts.policy.policyId,
    teacherRun: {
      root: relative(contracts.root, teacherRun.root).replaceAll('\\', '/'),
      contractHash: teacherRun.contractHash,
      receiptsHash: teacherRun.receiptsHash,
      taskBankHash: teacherRun.runContract.taskBankHash,
      policyHash: teacherRun.runContract.policyHash,
    },
    eligibleAcceptedLabelCount: eligibleAccepted.length,
    eligibleAcceptedLaneCounts,
    acceptedLabelCount: sourceRows.length,
    acceptedLaneCounts: Object.fromEntries(contracts.policy.lanes.map((lane) => [
      lane,
      sourceRows.filter((row) => row.lane === lane).length,
    ])),
    sourceRows,
    datasets,
  };
}

export function buildStudentLoraWorkload(contracts, adapterId, datasetPath, rowCount) {
  const adapter = contracts.policy.adapters.find((entry) => entry.id === adapterId);
  if (!adapter) {
    throw new Error(`Unknown student adapter ${adapterId}.`);
  }
  if (!Number.isInteger(rowCount) || rowCount < 1) {
    throw new Error(`Student adapter ${adapterId} requires at least one training row.`);
  }
  const training = contracts.policy.training;
  const workloadId = `student-code-${adapterId}-${contracts.policy.baseModel.id}`;
  return {
    schemaVersion: 1,
    kind: 'lora',
    id: workloadId,
    description: `Constructive Doppler ${adapterId} code-repair student experiment.`,
    claimBoundary: contracts.policy.claimBoundary,
    seed: contracts.policy.generation.seed,
    baseModelId: contracts.policy.baseModel.id,
    studentModelId: null,
    teacherModelId: 'machine-qualified-host-teacher',
    datasetId: `${workloadId}-labels`,
    datasetPath: resolve(datasetPath),
    evalDatasets: [{
      id: `${workloadId}-learning-receipt`,
      datasetPath: resolve(datasetPath),
      evalKind: 'text_generation',
      metrics: ['loss'],
      scoreboardColumns: [
        'loss',
        'baseline.loss',
        'qualityClaim.absoluteImprovement',
      ],
      quality: {
        baseline: 'base_model',
        requireImprovement: true,
        minAbsoluteImprovement: 1e-6,
        minRelativeImprovement: 0,
      },
      sourceLangs: [],
      targetLangs: [],
      pairAllowlist: [],
    }],
    trainingSchemaVersion: 1,
    checkpointEvery: rowCount,
    selectionMetric: 'loss',
    selectionGoal: 'min',
    surfaceSupport: 'node',
    training: {
      optimizer: {
        type: 'adamw',
        lr: training.learningRate,
        beta1: 0.9,
        beta2: 0.999,
        eps: 1e-8,
        weightDecay: 0,
        scheduler: {
          enabled: false,
          type: 'constant',
          warmupSteps: 0,
          stepSize: 1,
          gamma: 1,
          totalSteps: rowCount,
          minLr: 0,
        },
      },
      batchSize: 1,
      accumSteps: 1,
      steps: rowCount,
      precision: {
        activations: 'f16',
        gradients: 'f16',
        loraParams: 'f32',
      },
      gradientClipping: {
        maxNorm: training.gradientMaxNorm,
      },
    },
    lora: {
      datasetFormat: 'text-pairs',
      taskType: 'text_generation',
      maxLength: training.maxLength,
      joinWith: '',
      adapter: {
        rank: training.rank,
        alpha: training.alpha,
        dropout: training.dropout,
        targetModules: training.targetModules,
      },
      freeze: {
        encoder: false,
        prior: false,
        decoder: false,
        base: true,
        lora: false,
      },
      export: {
        enabled: true,
        atCheckpoints: false,
        select: 'final',
        id: workloadId,
        name: `Doppler ${adapterId} code-repair adapter`,
        format: 'manifest_json',
      },
      activation: {
        enabled: false,
        autoActivate: false,
        smokePrompt: 'Repair one Doppler defect.',
      },
    },
  };
}

export async function writeJsonArtifact(path, value) {
  await mkdir(dirname(path), { recursive: true });
  await writeFile(path, `${JSON.stringify(value, null, 2)}\n`, 'utf8');
  return path;
}

export async function writeJsonlArtifact(path, rows) {
  await mkdir(dirname(path), { recursive: true });
  const serialized = rows.map((row) => JSON.stringify(row)).join('\n');
  await writeFile(path, serialized ? `${serialized}\n` : '', 'utf8');
  return path;
}

export function selectStudentHoldoutTasks(contracts, lanes = null) {
  return selectHostTeacherTasks(contracts.host.taskBank, {
    lanes: lanes || contracts.policy.lanes,
    splits: [contracts.policy.holdoutSplit],
  });
}

export async function verifyStudentCodeExperimentContracts(options = {}) {
  const contracts = await loadStudentCodeExperimentContracts(options);
  const errors = [];
  if (contracts.policy.releaseTarget !== '0.4.9') {
    errors.push('releaseTarget must keep this experiment in 0.4.9 scope');
  }
  if (contracts.policy.holdoutSplit !== 'student_holdout') {
    errors.push('holdoutSplit must be student_holdout');
  }
  for (const lane of contracts.policy.lanes) {
    const labels = contracts.host.taskBank.tasks.filter((task) => (
      task.lane === lane && task.split === 'label'
    ));
    const holdouts = contracts.host.taskBank.tasks.filter((task) => (
      task.lane === lane && task.split === contracts.policy.holdoutSplit
    ));
    if (labels.length < 4) {
      errors.push(`${lane}: requires more than the original three label tasks`);
    }
    if (holdouts.length !== 2) {
      errors.push(`${lane}: requires exactly two reserved holdout tasks`);
    }
  }
  const labelCounts = contracts.policy.lanes.map((lane) => (
    contracts.host.taskBank.tasks.filter((task) => task.lane === lane && task.split === 'label').length
  ));
  if (new Set(labelCounts).size !== 1) {
    errors.push(`label task counts must be balanced, observed ${labelCounts.join(', ')}`);
  }
  const modelManifestPath = resolve(
    contracts.root,
    'models',
    'local',
    contracts.policy.baseModel.id,
    'manifest.json'
  );
  try {
    const manifest = JSON.parse(await readFile(modelManifestPath, 'utf8'));
    if (manifest.modelId !== contracts.policy.baseModel.id) {
      errors.push('base model manifest identity does not match the policy');
    }
    if (manifest.inference?.chatTemplate?.type !== contracts.policy.baseModel.chatTemplate) {
      errors.push('base model chat template does not match the policy');
    }
  } catch (error) {
    errors.push(`base model manifest is not readable: ${error.message}`);
  }
  const holdoutTasks = selectStudentHoldoutTasks(contracts);
  for (const task of holdoutTasks) {
    try {
      // Static prompt audit proves the renderer consumes only the mutated snapshot.
      // eslint-disable-next-line no-await-in-loop
      const prompt = await renderStudentTaskPrompt(contracts, task);
      for (const mutation of task.mutations) {
        if (!prompt.includes(mutation.replace)) {
          errors.push(`${task.id}: prompt omits the defective source text`);
        }
        if (mutation.find !== mutation.replace && prompt.includes(mutation.find)) {
          errors.push(`${task.id}: prompt exposes the exact holdout recovery text`);
        }
      }
    } catch (error) {
      errors.push(`${task.id}: prompt rendering failed: ${error.message}`);
    }
  }
  return {
    ok: errors.length === 0,
    policyId: contracts.policy.policyId,
    policyHash: contracts.policyHash,
    harnessHash: contracts.harnessHash,
    releaseTarget: contracts.policy.releaseTarget,
    taskBankId: contracts.host.taskBank.bankId,
    taskBankHash: contracts.host.taskBankArtifact.hash,
    baseRevision: contracts.host.taskBank.baseRevision,
    baseModelId: contracts.policy.baseModel.id,
    labelTasks: Object.fromEntries(contracts.policy.lanes.map((lane) => [
      lane,
      contracts.host.taskBank.tasks.filter((task) => task.lane === lane && task.split === 'label').length,
    ])),
    holdoutTasks: holdoutTasks.length,
    adapters: contracts.policy.adapters.map((adapter) => adapter.id),
    challengers: contracts.policy.challengers.map((challenger) => challenger.id),
    errors,
  };
}
