import { applyWgslRepairResponse } from '../../src/experimental/training/wgsl-repair.js';
import {
  evaluateNumericAgreement,
  hashWgslSemanticEvidenceValue,
} from '../../src/tooling/wgsl-repair-semantic-gate.js';

const PREFIX_CANARY_ELEMENTS = 16;
const SUFFIX_CANARY_ELEMENTS = 16;
const OUTPUT_CANARY = Math.fround(-4096.25);
const FLOAT32_TOLERANCE = Object.freeze({
  mode: 'numeric',
  absTolerance: 0.00001,
  relTolerance: 0.0001,
});

function isPlainObject(value) {
  return value != null && typeof value === 'object' && !Array.isArray(value);
}

function requirePositiveInteger(value, label) {
  const parsed = Number(value);
  if (!Number.isInteger(parsed) || parsed < 1) {
    throw new Error(`${label} must be an integer >= 1.`);
  }
  return parsed;
}

function toFloat32Bytes(values) {
  const typed = Float32Array.from(values, Math.fround);
  return [...new Uint8Array(typed.buffer)];
}

function fromFloat32Bytes(bytes) {
  const copied = Uint8Array.from(bytes);
  if (copied.byteLength % Float32Array.BYTES_PER_ELEMENT !== 0) {
    throw new Error('WGSL semantic harness: f32 readback byte length is invalid.');
  }
  return [...new Float32Array(copied.buffer)];
}

function toUniformBytes(fields) {
  const bytes = new Uint8Array(16);
  const view = new DataView(bytes.buffer);
  view.setUint32(0, fields.length, true);
  view.setUint32(4, fields.outputOffset, true);
  view.setFloat32(8, fields.first, true);
  view.setFloat32(12, fields.second, true);
  return [...bytes];
}

function generatedValue(seed, channel, index) {
  const mixed = (
    Math.imul(index + 1, 1664525)
    + Math.imul(seed + channel * 101, 1013904223)
  ) >>> 0;
  return Math.fround(((mixed % 2001) - 1000) / 113);
}

function generateValues(length, seed, channel) {
  return Array.from({ length }, (_, index) => generatedValue(seed, channel, index));
}

function reverseInputs(inputs) {
  return Object.fromEntries(Object.entries(inputs).map(([name, values]) => (
    [name, [...values].reverse()]
  )));
}

function allValuesEqual(values, expected) {
  return values.every((value) => Object.is(value, expected) || value === expected);
}

function createOracleDefinition(task, length) {
  const parameters = task.parameters || {};
  const unaryInputs = () => ({ inputValues: generateValues(length, task.inputSeed, 0) });
  const binaryInputs = () => ({
    leftValues: generateValues(length, task.inputSeed, 0),
    rightValues: generateValues(length, task.inputSeed, 1),
  });
  const unaryDefinition = (expected, first = 0, second = 0) => {
    const inputs = unaryInputs();
    return {
      inputs,
      inputBindings: [{ binding: 0, name: 'inputValues' }],
      outputBinding: 1,
      paramsBinding: 2,
      uniformFields: { first, second },
      expected,
    };
  };
  const binaryDefinition = (expected, first = 0, second = 0) => {
    const inputs = binaryInputs();
    return {
      inputs,
      inputBindings: [
        { binding: 0, name: 'leftValues' },
        { binding: 1, name: 'rightValues' },
      ],
      outputBinding: 2,
      paramsBinding: 3,
      uniformFields: { first, second },
      expected,
    };
  };
  if (task.oracleId === 'affine_f32') {
    const inputs = { inputValues: generateValues(length, task.inputSeed, 0) };
    return {
      inputs,
      inputBindings: [{ binding: 0, name: 'inputValues' }],
      outputBinding: 1,
      paramsBinding: 2,
      uniformFields: {
        first: Number(parameters.scale),
        second: Number(parameters.bias),
      },
      expected: (currentInputs) => currentInputs.inputValues.map((value) => (
        Math.fround(Math.fround(value * parameters.scale) + parameters.bias)
      )),
    };
  }
  if (task.oracleId === 'saxpy_f32') {
    const inputs = {
      leftValues: generateValues(length, task.inputSeed, 0),
      rightValues: generateValues(length, task.inputSeed, 1),
    };
    return {
      inputs,
      inputBindings: [
        { binding: 0, name: 'leftValues' },
        { binding: 1, name: 'rightValues' },
      ],
      outputBinding: 2,
      paramsBinding: 3,
      uniformFields: { first: Number(parameters.scale), second: 0 },
      expected: (currentInputs) => currentInputs.leftValues.map((value, index) => (
        Math.fround(value + Math.fround(parameters.scale * currentInputs.rightValues[index]))
      )),
    };
  }
  if (task.oracleId === 'clamp_f32') {
    const inputs = { inputValues: generateValues(length, task.inputSeed, 0) };
    return {
      inputs,
      inputBindings: [{ binding: 0, name: 'inputValues' }],
      outputBinding: 1,
      paramsBinding: 2,
      uniformFields: {
        first: Number(parameters.lower),
        second: Number(parameters.upper),
      },
      expected: (currentInputs) => currentInputs.inputValues.map((value) => (
        Math.fround(Math.min(parameters.upper, Math.max(parameters.lower, value)))
      )),
    };
  }
  if (task.oracleId === 'add_f32') {
    return binaryDefinition((inputs) => inputs.leftValues.map((value, index) => (
      Math.fround(value + inputs.rightValues[index])
    )));
  }
  if (task.oracleId === 'scale_f32') {
    return unaryDefinition(
      (inputs) => inputs.inputValues.map((value) => Math.fround(value * parameters.scale)),
      Number(parameters.scale)
    );
  }
  if (task.oracleId === 'relu_f32') {
    return unaryDefinition((inputs) => inputs.inputValues.map((value) => (
      Math.fround(Math.max(value, 0))
    )));
  }
  if (task.oracleId === 'subtract_f32') {
    return binaryDefinition((inputs) => inputs.leftValues.map((value, index) => (
      Math.fround(value - inputs.rightValues[index])
    )));
  }
  if (task.oracleId === 'mix_f32') {
    return binaryDefinition(
      (inputs) => inputs.leftValues.map((value, index) => {
        const oneMinusAlpha = Math.fround(1 - parameters.alpha);
        return Math.fround(
          Math.fround(value * oneMinusAlpha)
            + Math.fround(inputs.rightValues[index] * parameters.alpha)
        );
      }),
      Number(parameters.alpha)
    );
  }
  if (task.oracleId === 'square_bias_f32') {
    return unaryDefinition(
      (inputs) => inputs.inputValues.map((value) => (
        Math.fround(Math.fround(value * value) + parameters.bias)
      )),
      Number(parameters.bias)
    );
  }
  if (task.oracleId === 'absolute_f32') {
    return unaryDefinition((inputs) => inputs.inputValues.map((value) => (
      Math.fround(Math.abs(value))
    )));
  }
  if (task.oracleId === 'min_pair_f32') {
    return binaryDefinition((inputs) => inputs.leftValues.map((value, index) => (
      Math.fround(Math.min(value, inputs.rightValues[index]))
    )));
  }
  if (task.oracleId === 'threshold_negate_f32') {
    return unaryDefinition(
      (inputs) => inputs.inputValues.map((value) => (
        Math.fround(value < parameters.threshold ? -value : value)
      )),
      Number(parameters.threshold)
    );
  }
  if (task.oracleId === 'multiply_pair_f32') {
    return binaryDefinition((inputs) => inputs.leftValues.map((value, index) => (
      Math.fround(value * inputs.rightValues[index])
    )));
  }
  if (task.oracleId === 'max_pair_f32') {
    return binaryDefinition((inputs) => inputs.leftValues.map((value, index) => (
      Math.fround(Math.max(value, inputs.rightValues[index]))
    )));
  }
  if (task.oracleId === 'mean_pair_f32') {
    return binaryDefinition((inputs) => inputs.leftValues.map((value, index) => (
      Math.fround(Math.fround(value + inputs.rightValues[index]) * 0.5)
    )));
  }
  if (task.oracleId === 'distance_pair_f32') {
    return binaryDefinition((inputs) => inputs.leftValues.map((value, index) => (
      Math.fround(Math.abs(Math.fround(value - inputs.rightValues[index])))
    )));
  }
  if (task.oracleId === 'negate_f32') {
    return unaryDefinition((inputs) => inputs.inputValues.map((value) => (
      Math.fround(-value)
    )));
  }
  if (task.oracleId === 'floor_f32') {
    return unaryDefinition((inputs) => inputs.inputValues.map((value) => (
      Math.fround(Math.floor(value))
    )));
  }
  if (task.oracleId === 'add_scalar_f32') {
    return unaryDefinition(
      (inputs) => inputs.inputValues.map((value) => (
        Math.fround(value + parameters.scalar)
      )),
      Number(parameters.scalar)
    );
  }
  if (task.oracleId === 'leaky_relu_f32') {
    return unaryDefinition(
      (inputs) => inputs.inputValues.map((value) => (
        Math.fround(value >= 0 ? value : Math.fround(parameters.slope * value))
      )),
      Number(parameters.slope)
    );
  }
  if (task.oracleId === 'cap_f32') {
    return unaryDefinition(
      (inputs) => inputs.inputValues.map((value) => (
        Math.fround(Math.min(value, parameters.cap))
      )),
      Number(parameters.cap)
    );
  }
  if (task.oracleId === 'mask_below_f32') {
    return unaryDefinition(
      (inputs) => inputs.inputValues.map((value) => (
        Math.fround(value >= parameters.threshold ? value : 0)
      )),
      Number(parameters.threshold)
    );
  }
  if (task.oracleId === 'difference_scale_f32') {
    return binaryDefinition(
      (inputs) => inputs.leftValues.map((value, index) => (
        Math.fround(
          Math.fround(value - inputs.rightValues[index]) * parameters.scale
        )
      )),
      Number(parameters.scale)
    );
  }
  if (task.oracleId === 'square_scale_f32') {
    return unaryDefinition(
      (inputs) => inputs.inputValues.map((value) => (
        Math.fround(Math.fround(value * value) * parameters.scale)
      )),
      Number(parameters.scale)
    );
  }
  throw new Error(`WGSL semantic harness: unsupported oracle ${task.oracleId}.`);
}

function createDispatchInput(input) {
  const length = requirePositiveInteger(input.variant.length, 'variant.length');
  const workgroupSize = requirePositiveInteger(input.workgroupSize, 'workgroupSize');
  const dispatchWorkgroups = Math.ceil(length / workgroupSize);
  const dispatchedElements = dispatchWorkgroups * workgroupSize;
  const outputPaddingElements = Math.max(8, dispatchedElements - length);
  const outputOffset = PREFIX_CANARY_ELEMENTS;
  const outputElements = outputOffset
    + length
    + outputPaddingElements
    + SUFFIX_CANARY_ELEMENTS;
  const initialOutput = Array(outputElements).fill(OUTPUT_CANARY);
  const buffers = input.oracle.inputBindings.map(({ binding, name }) => ({
    binding,
    kind: 'read-only-storage',
    bytes: toFloat32Bytes(input.inputs[name]),
    readback: true,
  }));
  buffers.push({
    binding: input.oracle.outputBinding,
    kind: 'storage',
    bytes: toFloat32Bytes(initialOutput),
    readback: true,
  });
  buffers.push({
    binding: input.oracle.paramsBinding,
    kind: 'uniform',
    bytes: toUniformBytes({
      length,
      outputOffset,
      ...input.oracle.uniformFields,
    }),
    readback: false,
  });
  return {
    request: {
      id: input.id,
      code: input.code,
      entryPoint: 'main',
      constants: { WORKGROUP_SIZE: workgroupSize },
      dispatch: [dispatchWorkgroups, 1, 1],
      buffers,
    },
    layout: {
      length,
      outputOffset,
      outputPaddingElements,
      outputElements,
      initialOutput,
    },
  };
}

function bytesEqual(left, right) {
  return left.length === right.length && left.every((value, index) => value === right[index]);
}

function interpretDispatch(dispatchResult, prepared, oracle, inputs) {
  const outputBytes = dispatchResult.readbacks?.[String(oracle.outputBinding)]?.bytes || [];
  const outputValues = fromFloat32Bytes(outputBytes);
  const { length, outputOffset, outputPaddingElements } = prepared.layout;
  const logicalEnd = outputOffset + length;
  const paddingEnd = logicalEnd + outputPaddingElements;
  const actual = outputValues.slice(outputOffset, logicalEnd);
  const expected = oracle.expected(inputs);
  const readOnlyBuffersUnchanged = oracle.inputBindings.every(({ binding, name }) => {
    const actualBytes = dispatchResult.readbacks?.[String(binding)]?.bytes || [];
    return bytesEqual(actualBytes, toFloat32Bytes(inputs[name]));
  });
  return {
    dispatchResult,
    inputs,
    expected,
    actual,
    bounds: {
      prefixCanaryIntact: allValuesEqual(outputValues.slice(0, outputOffset), OUTPUT_CANARY),
      suffixCanaryIntact: allValuesEqual(outputValues.slice(paddingEnd), OUTPUT_CANARY),
      readOnlyBuffersUnchanged,
      outputPaddingUnchanged: allValuesEqual(
        outputValues.slice(logicalEnd, paddingEnd),
        OUTPUT_CANARY
      ),
      validationErrorsAbsent: dispatchResult.validationErrorsAbsent === true,
    },
  };
}

function relationResult(id, agreement, requiredChecks, evidence) {
  const pass = agreement.pass && requiredChecks.every(Boolean);
  return {
    id,
    status: pass ? 'pass' : 'fail',
    evidenceSha256: hashWgslSemanticEvidenceValue(evidence),
  };
}

async function runVariant(verifier, task, code, variant) {
  const oracle = createOracleDefinition(task, variant.length);
  const permutedInputs = reverseInputs(oracle.inputs);
  const alternateWorkgroupSize = variant.workgroupSize === 32 ? 64 : 32;
  const prepared = [
    createDispatchInput({
      id: `${task.taskId}-${variant.shapeId}-base`,
      code,
      variant,
      workgroupSize: variant.workgroupSize,
      oracle,
      inputs: oracle.inputs,
    }),
    createDispatchInput({
      id: `${task.taskId}-${variant.shapeId}-permuted`,
      code,
      variant,
      workgroupSize: variant.workgroupSize,
      oracle,
      inputs: permutedInputs,
    }),
    createDispatchInput({
      id: `${task.taskId}-${variant.shapeId}-alternate-workgroup`,
      code,
      variant,
      workgroupSize: alternateWorkgroupSize,
      oracle,
      inputs: oracle.inputs,
    }),
  ];
  const dispatchResults = await verifier.dispatch(prepared.map((entry) => entry.request));
  if (dispatchResults.length !== prepared.length) {
    throw new Error(`WGSL semantic harness: missing dispatch result for ${task.taskId}.`);
  }
  const base = interpretDispatch(dispatchResults[0], prepared[0], oracle, oracle.inputs);
  const permuted = interpretDispatch(dispatchResults[1], prepared[1], oracle, permutedInputs);
  const alternate = interpretDispatch(dispatchResults[2], prepared[2], oracle, oracle.inputs);
  const expectedPermutation = [...base.actual].reverse();
  const permutationAgreement = evaluateNumericAgreement(
    expectedPermutation,
    permuted.actual,
    FLOAT32_TOLERANCE
  );
  const tilingAgreement = evaluateNumericAgreement(
    base.actual,
    alternate.actual,
    FLOAT32_TOLERANCE
  );
  const metamorphic = [
    relationResult(
      'input_permutation_equivariance',
      permutationAgreement,
      [base.dispatchResult.passed, permuted.dispatchResult.passed],
      {
        baseActualSha256: hashWgslSemanticEvidenceValue(base.actual),
        permutedActualSha256: hashWgslSemanticEvidenceValue(permuted.actual),
        agreement: permutationAgreement,
      }
    ),
    relationResult(
      'tiling_equivalence',
      tilingAgreement,
      [base.dispatchResult.passed, alternate.dispatchResult.passed],
      {
        baseWorkgroupSize: variant.workgroupSize,
        alternateWorkgroupSize,
        baseActualSha256: hashWgslSemanticEvidenceValue(base.actual),
        alternateActualSha256: hashWgslSemanticEvidenceValue(alternate.actual),
        agreement: tilingAgreement,
      }
    ),
  ];
  return {
    shapeId: variant.shapeId,
    shapeClass: variant.shapeClass,
    workgroupId: variant.workgroupId,
    dispatch: {
      status: base.dispatchResult.passed ? 'pass' : 'fail',
      backend: 'chromium_webgpu',
      workgroupSize: variant.workgroupSize,
      workgroups: prepared[0].request.dispatch,
      runtimeErrors: base.dispatchResult.runtimeErrors,
    },
    compilation: base.dispatchResult.compilation,
    oracle: {
      revision: 'wgsl-semantic-cpu-oracles-v1',
      inputs: base.inputs,
      inputSha256: hashWgslSemanticEvidenceValue(base.inputs),
      expected: base.expected,
      expectedSha256: hashWgslSemanticEvidenceValue(base.expected),
      actual: base.actual,
      actualSha256: hashWgslSemanticEvidenceValue(base.actual),
      tolerance: FLOAT32_TOLERANCE,
    },
    bufferBounds: base.bounds,
    metamorphic,
    supportingDispatches: {
      permutationPass: permuted.dispatchResult.passed,
      alternateWorkgroupPass: alternate.dispatchResult.passed,
    },
  };
}

function buildTaskFromSource(task, source) {
  const start = source.indexOf(task.brokenSpan);
  if (start < 0 || source.indexOf(task.brokenSpan, start + 1) >= 0) {
    throw new Error(`WGSL semantic harness: ${task.taskId} broken span must occur exactly once.`);
  }
  return {
    taskId: task.taskId,
    source,
    span: {
      start,
      end: start + task.brokenSpan.length,
      broken: task.brokenSpan,
      reference: task.referenceSpan,
    },
  };
}

function historicalRegressionResults(variants) {
  const logicalExtentPass = variants.every((variant) => (
    variant.bufferBounds.prefixCanaryIntact
    && variant.bufferBounds.suffixCanaryIntact
    && variant.bufferBounds.outputPaddingUnchanged
    && variant.oracle.actual.length === variant.oracle.expected.length
  ));
  const readOnlyPass = variants.every((variant) => (
    variant.bufferBounds.readOnlyBuffersUnchanged
  ));
  return [
    {
      id: 'logical-elements-not-padded-storage',
      status: logicalExtentPass ? 'pass' : 'fail',
    },
    {
      id: 'readonly-input-byte-identity',
      status: readOnlyPass ? 'pass' : 'fail',
    },
  ];
}

export async function runWgslSemanticTaskManifest(options) {
  const manifest = options.manifest;
  const verifier = options.verifier;
  if (!isPlainObject(manifest)
    || manifest.schema !== 'doppler.wgsl-repair-semantic-task-manifest/v1'
    || !Array.isArray(manifest.tasks)
    || manifest.tasks.length === 0
    || typeof verifier?.dispatch !== 'function') {
    throw new Error('WGSL semantic harness: manifest and dispatch verifier are required.');
  }
  const completions = options.completions || {};
  const mode = options.mode || 'reference';
  if (!['reference', 'candidate'].includes(mode)) {
    throw new Error('WGSL semantic harness: mode must be reference or candidate.');
  }
  const evidence = [];
  for (const task of manifest.tasks) {
    const source = options.sources?.[task.taskId];
    if (typeof source !== 'string' || source.length === 0) {
      throw new Error(`WGSL semantic harness: source missing for ${task.taskId}.`);
    }
    const completion = mode === 'reference' ? task.referenceSpan : completions[task.taskId];
    if (typeof completion !== 'string') {
      throw new Error(`WGSL semantic harness: completion missing for ${task.taskId}.`);
    }
    const repairTask = buildTaskFromSource(task, source);
    const applied = applyWgslRepairResponse(repairTask, completion);
    const variants = [];
    for (const variant of task.variants) {
      variants.push(await runVariant(verifier, task, applied.candidateSource, variant));
    }
    const regressionResults = historicalRegressionResults(variants);
    const allCompilationsPass = variants.every((variant) => (
      variant.compilation?.passed === true
    ));
    evidence.push({
      taskId: task.taskId,
      kernelFamilyId: task.kernelFamilyId,
      role: manifest.role,
      responseContractPass: applied.ok,
      responseContractViolations: applied.violations,
      completionSha256: hashWgslSemanticEvidenceValue(completion),
      exactReferenceCompletion: completion === task.referenceSpan,
      candidateSourceSha256: applied.candidateSha256,
      compilation: { status: allCompilationsPass ? 'pass' : 'fail' },
      variants,
      historicalRegressionsPass: regressionResults.every((entry) => entry.status === 'pass'),
      historicalRegressionResults: regressionResults,
    });
  }
  return evidence;
}

export function summarizeWgslSemanticTaskEvidence(taskResults) {
  const tasks = Array.isArray(taskResults) ? taskResults : [];
  return {
    taskCount: tasks.length,
    responseContractPasses: tasks.filter((task) => task.responseContractPass === true).length,
    compilationPasses: tasks.filter((task) => task.compilation?.status === 'pass').length,
    dispatchVariantCount: tasks.reduce((sum, task) => sum + (task.variants?.length || 0), 0),
    dispatchVariantPasses: tasks.reduce((sum, task) => (
      sum + (task.variants || []).filter((variant) => variant.dispatch?.status === 'pass').length
    ), 0),
    historicalRegressionPasses: tasks.filter((task) => (
      task.historicalRegressionsPass === true
    )).length,
  };
}
