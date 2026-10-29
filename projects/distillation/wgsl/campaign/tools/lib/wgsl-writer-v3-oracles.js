import { hashWgslSemanticEvidenceValue } from '../../src/tooling/wgsl-repair-semantic-gate.js';

function decode32(bytes, kind, label) {
  if (!Array.isArray(bytes) || bytes.length % 4 !== 0) {
    throw new Error(`${label} output bytes are not 32-bit aligned.`);
  }
  const copied = Uint8Array.from(bytes);
  const view = new DataView(copied.buffer);
  return Array.from({ length: copied.length / 4 }, (_, index) => (
    kind === 'f32'
      ? view.getFloat32(index * 4, true)
      : view.getUint32(index * 4, true)
  ));
}

function evaluateFloat32(oracle, output) {
  const actual = decode32(output?.bytes, 'f32', oracle.resourceId);
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
  return {
    pass: actual.length === expected.length && comparisons.every((entry) => entry.pass),
    kind: oracle.kind,
    resourceId: oracle.resourceId,
    expectedLength: expected.length,
    actualLength: actual.length,
    comparisons,
  };
}

function evaluateUint32(oracle, output) {
  const actual = decode32(output?.bytes, 'u32', oracle.resourceId);
  const expected = oracle.expected.map(Number);
  const mismatches = expected.flatMap((reference, index) => (
    actual[index] === reference ? [] : [{ index, expected: reference, actual: actual[index] }]
  ));
  return {
    pass: actual.length === expected.length && mismatches.length === 0,
    kind: oracle.kind,
    resourceId: oracle.resourceId,
    expectedLength: expected.length,
    actualLength: actual.length,
    mismatches,
  };
}

function evaluateBytes(oracle, output) {
  const actual = Array.isArray(output?.bytes) ? output.bytes.map(Number) : [];
  const expected = oracle.expected.map(Number);
  const mismatches = expected.flatMap((reference, index) => (
    actual[index] === reference ? [] : [{ index, expected: reference, actual: actual[index] }]
  ));
  return {
    pass: actual.length === expected.length && mismatches.length === 0,
    kind: oracle.kind,
    resourceId: oracle.resourceId,
    expectedLength: expected.length,
    actualLength: actual.length,
    mismatches,
    outputSha256: hashWgslSemanticEvidenceValue(actual),
  };
}

export function evaluateWgslWriterV3Oracle(oracle, execution) {
  const output = execution?.outputs?.[oracle?.resourceId];
  if (oracle?.kind === 'f32_sequence') return evaluateFloat32(oracle, output);
  if (oracle?.kind === 'u32_sequence') return evaluateUint32(oracle, output);
  if (oracle?.kind === 'rgba8_exact') return evaluateBytes(oracle, output);
  throw new Error(`WGSL writer v3 oracle is unsupported: ${oracle?.kind}.`);
}
