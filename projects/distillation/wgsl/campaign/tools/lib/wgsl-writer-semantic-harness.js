import { hashWgslSemanticEvidenceValue } from '../../src/tooling/wgsl-repair-semantic-gate.js';
import {
  runWgslSemanticTaskManifest,
  summarizeWgslSemanticTaskEvidence,
} from './wgsl-semantic-harness.js';

export { summarizeWgslSemanticTaskEvidence };

function isPlainObject(value) {
  return value != null && typeof value === 'object' && !Array.isArray(value);
}

function escapeRegExp(value) {
  return String(value).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

export function parseCompleteWgslResponse(response, contract, interfaceContract) {
  const violations = [];
  if (typeof response !== 'string') violations.push('non_string_response');
  const source = typeof response === 'string' ? response.trim() : '';
  if (!source) violations.push('empty_shader');
  if (source.length > Number(contract?.maxCharacters)) {
    violations.push('shader_character_limit_exceeded');
  }
  if (contract?.forbidMarkdownFences === true && source.includes('```')) {
    violations.push('markdown_fence');
  }
  if (contract?.requireComputeStage === true && !/@compute\b/.test(source)) {
    violations.push('compute_stage_absent');
  }
  const entryPoint = String(interfaceContract?.entryPoint || '');
  if (!entryPoint
    || !new RegExp(`\\bfn\\s+${escapeRegExp(entryPoint)}\\s*\\(`).test(source)) {
    violations.push('required_entry_point_absent');
  }
  for (const requiredOverride of interfaceContract?.requiredOverrides || []) {
    const name = String(requiredOverride?.name || '');
    if (!name || !new RegExp(`\\boverride\\s+${escapeRegExp(name)}\\b`).test(source)) {
      violations.push(`required_override_absent:${name || 'unknown'}`);
    }
  }
  return {
    ok: violations.length === 0,
    source,
    violations,
  };
}

export function buildWgslWriterPrompt(task, promptContract) {
  if (!isPlainObject(task)
    || typeof task.specification !== 'string'
    || !isPlainObject(task.interfaceContract)) {
    throw new Error('WGSL writer prompt: task specification and interface contract are required.');
  }
  if (promptContract?.responseContract !== 'complete_wgsl_compute_shader_only_v1') {
    throw new Error('WGSL writer prompt: unsupported response contract.');
  }
  return [
    'Author one complete WGSL compute shader from the supplied contract.',
    'Return only the complete WGSL source; no Markdown fence, diff, or explanation.',
    'The shader must implement every binding, entry-point, dispatch, bounds, and arithmetic requirement exactly.',
    `<task_id>${task.taskId}</task_id>`,
    '<specification>',
    task.specification.trim(),
    '</specification>',
    '<interface_contract>',
    JSON.stringify(task.interfaceContract, null, 2),
    '</interface_contract>',
  ].join('\n');
}

export async function runWgslWriterTaskManifest(options) {
  const manifest = options.manifest;
  const verifier = options.verifier;
  if (!isPlainObject(manifest)
    || manifest.schema !== 'doppler.wgsl-writer-task-manifest/v1'
    || !Array.isArray(manifest.tasks)
    || manifest.tasks.length === 0
    || typeof verifier?.dispatch !== 'function') {
    throw new Error('WGSL writer semantic harness: manifest and dispatch verifier are required.');
  }
  const mode = options.mode || 'reference';
  if (!['reference', 'candidate'].includes(mode)) {
    throw new Error('WGSL writer semantic harness: mode must be reference or candidate.');
  }
  const referenceShaders = options.referenceShaders || {};
  const candidateCompletions = options.completions || {};
  const parsedByTask = {};
  const sources = {};
  const completions = {};
  const adaptedTasks = [];
  for (const task of manifest.tasks) {
    const referenceShader = referenceShaders[task.taskId];
    if (typeof referenceShader !== 'string' || referenceShader.length === 0) {
      throw new Error(`WGSL writer semantic harness: reference missing for ${task.taskId}.`);
    }
    const completion = mode === 'reference'
      ? referenceShader
      : candidateCompletions[task.taskId];
    const parsed = parseCompleteWgslResponse(
      completion,
      options.responseContract,
      task.interfaceContract
    );
    const sentinel = `__DOPPLER_COMPLETE_SHADER_${task.taskId}__`;
    parsedByTask[task.taskId] = parsed;
    sources[task.taskId] = sentinel;
    completions[task.taskId] = parsed.source;
    adaptedTasks.push({
      ...task,
      brokenSpan: sentinel,
      referenceSpan: referenceShader.trim(),
    });
  }
  const adaptedManifest = {
    ...manifest,
    schema: 'doppler.wgsl-repair-semantic-task-manifest/v1',
    tasks: adaptedTasks,
  };
  const delegated = await runWgslSemanticTaskManifest({
    manifest: adaptedManifest,
    sources,
    mode: 'candidate',
    completions,
    verifier,
  });
  return delegated.map((task) => {
    const parsed = parsedByTask[task.taskId];
    const referenceShader = referenceShaders[task.taskId].trim();
    const responseContractViolations = [
      ...new Set([
        ...(task.responseContractViolations || []),
        ...parsed.violations,
      ]),
    ];
    return {
      ...task,
      responseContractPass: task.responseContractPass === true && parsed.ok,
      responseContractViolations,
      exactReferenceCompletion: parsed.source === referenceShader,
      referenceShaderSha256: hashWgslSemanticEvidenceValue(referenceShader),
    };
  });
}
