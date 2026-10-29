import { createHash } from 'node:crypto';
import fs from 'node:fs/promises';

import { hashWgslSemanticEvidenceValue } from '../../src/tooling/wgsl-repair-semantic-gate.js';
import { buildWgslAuthorExecutionPlan } from './wgsl-author-execution-plan.js';

function isPlainObject(value) {
  return value != null && typeof value === 'object' && !Array.isArray(value);
}

function sha256Bytes(bytes) {
  return createHash('sha256').update(bytes).digest('hex');
}

function encodeNumericValues(values, kind, label) {
  if (!Array.isArray(values)) throw new Error(`${label} values must be an array.`);
  const bytes = new Uint8Array(values.length * 4);
  const view = new DataView(bytes.buffer);
  for (let index = 0; index < values.length; index += 1) {
    const value = values[index];
    if (kind === 'f32_le') {
      if (!Number.isFinite(value)) throw new Error(`${label} contains a non-finite f32.`);
      view.setFloat32(index * 4, value, true);
    } else {
      if (!Number.isSafeInteger(value) || value < 0 || value > 0xffffffff) {
        throw new Error(`${label} contains an invalid u32.`);
      }
      view.setUint32(index * 4, value, true);
    }
  }
  return [...bytes];
}

function normalizeContextResources(resources, taskId) {
  if (!isPlainObject(resources)) throw new Error(`${taskId} resources must be an object.`);
  return Object.fromEntries(Object.entries(resources).map(([resourceId, resource]) => {
    const label = `${taskId}.${resourceId}`;
    if (resource?.initialization === 'zero') {
      return [resourceId, { initialization: 'zero' }];
    }
    if (resource?.initialization === 'f32_le' || resource?.initialization === 'u32_le') {
      return [resourceId, {
        initialization: 'bytes',
        bytes: encodeNumericValues(resource.values, resource.initialization, label),
      }];
    }
    throw new Error(`${label} initialization is unsupported.`);
  }));
}

async function hydrateModules(modules, taskId) {
  if (!Array.isArray(modules) || modules.length === 0) {
    throw new Error(`${taskId} reference module source is required.`);
  }
  const hydrated = [];
  const sourceBindings = [];
  for (const module of modules) {
    const path = String(module?.source?.path || '');
    const expectedSha256 = String(module?.source?.sha256 || '');
    const bytes = await fs.readFile(path);
    const actualSha256 = sha256Bytes(bytes);
    if (actualSha256 !== expectedSha256) {
      throw new Error(`${taskId}.${module?.id} source SHA-256 mismatch.`);
    }
    hydrated.push({ id: module.id, wgsl: bytes.toString('utf8').trim() });
    sourceBindings.push({ id: module.id, path, sha256: actualSha256 });
  }
  return { hydrated, sourceBindings };
}

export function validateWgslAuthorReferenceManifest(manifest) {
  if (!isPlainObject(manifest)
    || manifest.schema !== 'doppler.wgsl-author-reference-manifest/v1'
    || manifest.experimentId !== 'doppler-wgsl-writer-v3'
    || manifest.role !== 'mechanics_reference_qualification_only'
    || manifest.populationAuthority !== 'none'
    || manifest.license !== 'Apache-2.0'
    || !isPlainObject(manifest.runtime)
    || typeof manifest.runtime.headless !== 'boolean'
    || typeof manifest.runtime.requiredBackend !== 'string'
    || manifest.runtime.requiredBackend.length === 0
    || (manifest.runtime.requiredVendor !== null
      && (typeof manifest.runtime.requiredVendor !== 'string'
        || manifest.runtime.requiredVendor.length === 0))
    || !Number.isSafeInteger(manifest.runtime.replayCount)
    || manifest.runtime.replayCount < 2
    || !Array.isArray(manifest.runtime.browserArgs)
    || manifest.runtime.browserArgs.length === 0
    || !Array.isArray(manifest.runtime.requiredFeatures)
    || !isPlainObject(manifest.runtime.requiredLimits)
    || !isPlainObject(manifest.allocationLimits)
    || !Array.isArray(manifest.tasks)
    || manifest.tasks.length !== 4) {
    throw new Error('WGSL author reference manifest is invalid.');
  }
  const taskIds = new Set();
  const pipelineKinds = new Set();
  for (const task of manifest.tasks) {
    if (typeof task?.taskId !== 'string' || taskIds.has(task.taskId)) {
      throw new Error(`WGSL author reference task id is invalid: ${task?.taskId}.`);
    }
    taskIds.add(task.taskId);
    if (!['compute', 'render', 'multi_pass'].includes(task.pipelineKind)) {
      throw new Error(`${task.taskId} pipeline kind is invalid.`);
    }
    pipelineKinds.add(task.pipelineKind);
    if (!isPlainObject(task.contract)
      || !isPlainObject(task.context)
      || !isPlainObject(task.packageTemplate)
      || !isPlainObject(task.oracle)) {
      throw new Error(`${task.taskId} reference contract is incomplete.`);
    }
  }
  for (const required of ['compute', 'render', 'multi_pass']) {
    if (!pipelineKinds.has(required)) {
      throw new Error(`WGSL author reference manifest is missing ${required}.`);
    }
  }
  return manifest;
}

export async function materializeWgslAuthorReferenceTask(task, manifest, formatCatalog) {
  const { hydrated, sourceBindings } = await hydrateModules(
    task.packageTemplate.modules,
    task.taskId
  );
  const packageValue = {
    ...structuredClone(task.packageTemplate),
    modules: hydrated,
  };
  const contract = {
    ...structuredClone(task.contract),
    availableFeatures: [...manifest.runtime.requiredFeatures],
    limits: structuredClone(manifest.runtime.requiredLimits),
    allocationLimits: structuredClone(manifest.allocationLimits),
    formats: structuredClone(formatCatalog.formats),
  };
  const context = {
    parameters: structuredClone(task.context.parameters),
    overrides: structuredClone(task.context.overrides),
    resources: normalizeContextResources(task.context.resources, task.taskId),
  };
  const plan = buildWgslAuthorExecutionPlan(packageValue, contract, context);
  return {
    taskId: task.taskId,
    pipelineKind: task.pipelineKind,
    objective: task.objective,
    packageValue,
    packageSha256: hashWgslSemanticEvidenceValue(packageValue),
    sourceBindings,
    plan,
    planSha256: hashWgslSemanticEvidenceValue(plan),
    oracle: structuredClone(task.oracle),
  };
}

function decodeFloat32(bytes, label) {
  if (!Array.isArray(bytes) || bytes.length % 4 !== 0) {
    throw new Error(`${label} f32 output bytes are invalid.`);
  }
  const copied = Uint8Array.from(bytes);
  const view = new DataView(copied.buffer);
  return Array.from({ length: bytes.length / 4 }, (_, index) => (
    view.getFloat32(index * 4, true)
  ));
}

function evaluateFloat32Oracle(oracle, output) {
  const actual = decodeFloat32(output?.bytes, oracle.resourceId);
  const expected = oracle.expected.map(Number);
  const comparisons = expected.map((reference, index) => {
    const candidate = actual[index];
    const tolerance = Number(oracle.absTolerance)
      + Number(oracle.relTolerance) * Math.abs(reference);
    return {
      index,
      expected: reference,
      actual: candidate,
      error: Math.abs(candidate - reference),
      tolerance,
      pass: Number.isFinite(candidate) && Math.abs(candidate - reference) <= tolerance,
    };
  });
  const lengthExact = actual.length === expected.length;
  return {
    pass: lengthExact && comparisons.every((entry) => entry.pass),
    kind: oracle.kind,
    resourceId: oracle.resourceId,
    lengthExact,
    expected,
    actual,
    comparisons,
  };
}

function evaluateRgba8Oracle(oracle, output) {
  const bytes = Array.isArray(output?.bytes) ? output.bytes.map(Number) : [];
  const pixelAligned = bytes.length > 0 && bytes.length % 4 === 0;
  const mismatches = [];
  if (pixelAligned) {
    for (let offset = 0; offset < bytes.length; offset += 4) {
      for (let channel = 0; channel < 4; channel += 1) {
        const expected = Number(oracle.expectedPixel[channel]);
        const actual = bytes[offset + channel];
        if (Math.abs(actual - expected) > Number(oracle.channelTolerance)) {
          mismatches.push({ pixel: offset / 4, channel, expected, actual });
        }
      }
    }
  }
  return {
    pass: pixelAligned && mismatches.length === 0,
    kind: oracle.kind,
    resourceId: oracle.resourceId,
    pixels: pixelAligned ? bytes.length / 4 : 0,
    expectedPixel: [...oracle.expectedPixel],
    channelTolerance: oracle.channelTolerance,
    mismatches,
    outputSha256: hashWgslSemanticEvidenceValue(bytes),
  };
}

export function evaluateWgslAuthorReferenceOracle(oracle, execution) {
  const output = execution?.outputs?.[oracle?.resourceId];
  if (oracle?.kind === 'f32_sequence') return evaluateFloat32Oracle(oracle, output);
  if (oracle?.kind === 'rgba8_uniform') return evaluateRgba8Oracle(oracle, output);
  throw new Error(`WGSL author reference oracle is unsupported: ${oracle?.kind}.`);
}
