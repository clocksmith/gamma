// The ridge maximum is an unnormalized score. Cutoffs belong to the calibrated fit and its exact classifier.
const digest = async bytes => Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)),
  byte => byte.toString(16).padStart(2, '0')).join('');
const decode = bytes => JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(bytes));
const isDigest = value => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value);

export async function loadReadoutGate(headerBytes, gateBytes, expectedGateSha256) {
  if (!isDigest(expectedGateSha256) || await digest(gateBytes) !== expectedGateSha256) {
    throw new Error('Gate bytes differ from the pinned policy');
  }
  const header = decode(headerBytes), gate = decode(gateBytes);
  if (gate.schema !== 'gamma.readout-gate/v1' || gate.classifierHeaderSha256 !== await digest(headerBytes)
      || header.schema !== 'gamma.linear-classifier/v1' || header.dtype !== 'f16'
      || !Array.isArray(header.codes) || header.codes.length < 2
      || new Set(header.codes).size !== header.codes.length
      || !header.codes.every(code => typeof code === 'string' && code.length > 0)) {
    throw new Error('Gate differs from its frozen F16 classifier');
  }
  const calibration = gate.calibration;
  if (!calibration || !isDigest(calibration.fitScoresSha256)
      || calibration.baseManifestSha256 !== header.baseManifestSha256 || !isDigest(header.baseManifestSha256)
      || !Number.isSafeInteger(calibration.fitTables) || calibration.fitTables <= 0
      || !Number.isSafeInteger(calibration.fitRows) || calibration.fitRows < calibration.fitTables
      || !Number.isFinite(calibration.threshold)) throw new Error('Invalid readout calibration');
  const strict = calibration.rule === 'uncovered-false-accept-5pct-strict';
  if (!strict && calibration.rule !== 'lookup-rate-35pct-inclusive') throw new Error('Unknown cutoff rule');

  return scores => {
    if (scores.length !== header.codes.length || !Array.from(scores).every(Number.isFinite)) {
      throw new Error('Missing or nonfinite readout scores');
    }
    const score = Math.max(...scores);
    const direct = strict ? score > calibration.threshold : score >= calibration.threshold;
    return { action: direct ? 'answer' : 'lookup', code: direct ? header.codes[scores.indexOf(score)] : null, score };
  };
}
