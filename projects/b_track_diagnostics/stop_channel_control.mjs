// Development-only intervention on an already compiled v4 LoRA.
// No refitting, new targets, label lookup, or changes to sealed v4 code.
export function scaleCompiledStopChannel(lora, gain = 1) {
  if (!Number.isFinite(gain) || gain < 0 || gain > 1) {
    throw new RangeError('stop gain must be finite and within [0, 1]');
  }
  const targetCount = lora.uniqTargetTokens?.length;
  if (!Number.isInteger(targetCount) || lora.rank !== targetCount + 2) {
    throw new Error('Expected v4 target + suppress + stop rank layout');
  }
  if (!Number.isInteger(lora.dHidden) || lora.dHidden < 1) {
    throw new Error('Invalid hidden width');
  }
  const stopRow = targetCount + 1;
  const layers = new Map();
  for (const [id, entry] of lora.layers) {
    if (entry.rank !== lora.rank || entry.b.length !== lora.rank * lora.dHidden) {
      throw new Error('Invalid v4 B matrix layout');
    }
    const b = new Float32Array(entry.b);
    if (gain !== 1) {
      for (let j = 0; j < lora.dHidden; j += 1) {
        b[stopRow * lora.dHidden + j] *= gain;
      }
    }
    layers.set(id, { ...entry, a: new Float32Array(entry.a), b });
  }
  return { ...lora, layers };
}
