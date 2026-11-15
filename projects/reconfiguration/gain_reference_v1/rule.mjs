// CPU reference for prospective experiments, not a production inference path.
function finite(value, label) {
  if (!Number.isFinite(value)) throw new Error(`${label} must be finite`);
  return value;
}

function span(value, tokenCount, label) {
  if (!Array.isArray(value) || value.length !== 2 ||
      !value.every(Number.isSafeInteger) || value[0] < 0 ||
      value[0] >= value[1] || value[1] > tokenCount) {
    throw new Error(`${label} must be a nonempty half-open token span`);
  }
  return [...value];
}

// Instruction and reference tokens share the ORIGINAL full-prompt computation.
// Template tokens outside contentSpan contribute to neither statistic.
// This is NOT historical reference A (which deletes and re-prefills the span).
export function samePassEnergy({tokenCount, channels, instructionSpan, contentSpan}) {
  if (!Number.isSafeInteger(tokenCount) || tokenCount < 1 ||
      !Number.isSafeInteger(channels) || channels < 1) {
    throw new Error('Positive integer token and channel counts required');
  }
  const instruction = span(instructionSpan, tokenCount, 'instructionSpan');
  const content = span(contentSpan, tokenCount, 'contentSpan');
  if (instruction[0] < content[0] || instruction[1] > content[1]) {
    throw new Error('Instruction must be contained in content');
  }
  const instructionCount = instruction[1] - instruction[0];
  const referenceCount = content[1] - content[0] - instructionCount;
  if (!referenceCount) throw new Error('Empty complementary reference');
  const instr = new Float64Array(channels);
  const ref = new Float64Array(channels);
  let nextToken = 0;
  let closed = false;
  return {
    // One row at a time: O(channels) retained storage, not O(tokens*channels).
    add(tokenIndex, activations) {
      if (closed || tokenIndex !== nextToken || tokenIndex >= tokenCount) {
        throw new Error('Each original token must be supplied exactly once in order');
      }
      if (activations.length !== channels) throw new Error('Channel width changed');
      const target = tokenIndex < content[0] || tokenIndex >= content[1] ? null :
        tokenIndex >= instruction[0] && tokenIndex < instruction[1] ? instr : ref;
      // Validate the full row before changing state so rejected input is retryable.
      for (const value of activations) {
        finite(value, 'activation');
        finite(value * value, 'squared activation');
      }
      if (target) {
        for (let i = 0; i < channels; i++) {
          finite(target[i] + activations[i] ** 2, 'energy sum');
        }
        for (let i = 0; i < channels; i++) target[i] += activations[i] ** 2;
      }
      nextToken++;
    },
    finish() {
      if (closed || nextToken !== tokenCount) throw new Error('Incomplete or closed capture');
      closed = true;
      return {
        reference: 'same-pass-content-complement/v1',
        instructionEnergy: Float64Array.from(instr, x => x / instructionCount),
        referenceEnergy: Float64Array.from(ref, x => x / referenceCount),
        instructionCount, referenceCount,
        accumulatorBytes: instr.byteLength + ref.byteLength,
      };
    },
  };
}

// Also accepts independently frozen reference energies. Their provenance must be
// checked by the experiment runner; this function cannot prove model identity.
export function deriveGains(instructionEnergy, referenceEnergy, {beta, clip, epsilon}) {
  finite(beta, 'beta'); finite(clip, 'clip'); finite(epsilon, 'epsilon');
  if (clip <= 0 || epsilon <= 0 || !instructionEnergy.length ||
      instructionEnergy.length !== referenceEnergy.length) {
    throw new Error('Positive clip/epsilon and matching nonempty energies required');
  }
  const logGains = new Float64Array(instructionEnergy.length);
  let total = 0;
  for (let i = 0; i < logGains.length; i++) {
    const a = finite(instructionEnergy[i], 'instruction energy');
    const b = finite(referenceEnergy[i], 'reference energy');
    if (a < 0 || b < 0) throw new Error('Energy must be nonnegative');
    const denominator = finite(b + epsilon, 'reference denominator');
    const score = (a - b) / denominator;
    const bounded = Math.max(-clip, Math.min(clip, score));
    logGains[i] = finite(beta * bounded, 'log gain');
    total = finite(total + logGains[i], 'log gain sum');
  }
  const mean = total / logGains.length;
  const gains = Float64Array.from(logGains, x => Math.exp(x - mean));
  if (gains.some(x => !Number.isFinite(x) || x <= 0)) {
    throw new Error('Gain is not positive and finite');
  }
  return gains;
}
