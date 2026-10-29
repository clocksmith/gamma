function isObject(value) {
  return value != null && typeof value === 'object' && !Array.isArray(value);
}

function requireString(value, label) {
  const normalized = typeof value === 'string' ? value.trim() : '';
  if (!normalized) throw new Error(`${label} is required.`);
  return normalized;
}

function requireHash(value, label) {
  const normalized = requireString(value, label);
  if (!/^[a-f0-9]{64}$/.test(normalized)) {
    throw new Error(`${label} must be a SHA-256 digest.`);
  }
  return normalized;
}

function stableJson(value) {
  if (Array.isArray(value)) return `[${value.map(stableJson).join(',')}]`;
  if (isObject(value)) {
    return `{${Object.keys(value).sort().map((key) => (
      `${JSON.stringify(key)}:${stableJson(value[key])}`
    )).join(',')}}`;
  }
  return JSON.stringify(value);
}

function samplePassed(sample) {
  return sample?.rewardVector?.reduction?.scalarReward > 0;
}

function exactReferenceMatched(sample) {
  return sample?.rewardVector?.components?.some((component) => (
    component?.id === 'exact_reference_match' && component.normalizedValue === 1
  )) === true;
}

function requireGroups(groups, label) {
  if (!Array.isArray(groups) || groups.length === 0) {
    throw new Error(`${label} must contain at least one rollout group.`);
  }
  return groups;
}

function summarize(groups) {
  const samples = groups.flatMap((group) => group.samples);
  const passingSamples = samples.filter(samplePassed).length;
  const passingTasksAt1 = groups.filter((group) => samplePassed(group.samples[0])).length;
  const passingTasksAtK = groups.filter((group) => group.samples.some(samplePassed)).length;
  return {
    taskCount: groups.length,
    groupSize: groups[0].samples.length,
    sampleCount: samples.length,
    passingSamples,
    samplePassRate: passingSamples / samples.length,
    passingTasksAt1,
    passAt1: passingTasksAt1 / groups.length,
    passingTasksAtK,
    passAtK: passingTasksAtK / groups.length,
    exactReferenceSamples: samples.filter(exactReferenceMatched).length,
    blockedSamples: samples.filter((sample) => (
      sample?.rewardVector?.reduction?.blocked === true
    )).length,
  };
}

function validateDiscordantCounts(referenceOnly, candidateOnly) {
  if (!Number.isInteger(referenceOnly) || referenceOnly < 0
      || !Number.isInteger(candidateOnly) || candidateOnly < 0) {
    throw new Error('McNemar discordant counts must be non-negative integers.');
  }
}

function logAddExp(left, right) {
  if (left === -Infinity) return right;
  if (right === -Infinity) return left;
  const maximum = Math.max(left, right);
  return maximum + Math.log(Math.exp(left - maximum) + Math.exp(right - maximum));
}

export function exactMcNemarLogPValue(referenceOnly, candidateOnly) {
  validateDiscordantCounts(referenceOnly, candidateOnly);
  const discordant = referenceOnly + candidateOnly;
  if (discordant === 0) return 0;
  const tail = Math.min(referenceOnly, candidateOnly);
  let logProbability = -discordant * Math.log(2);
  let logCumulative = logProbability;
  for (let index = 1; index <= tail; index += 1) {
    logProbability += Math.log(discordant - index + 1) - Math.log(index);
    logCumulative = logAddExp(logCumulative, logProbability);
  }
  return Math.min(0, Math.log(2) + logCumulative);
}

export function exactMcNemarPValue(referenceOnly, candidateOnly) {
  return Math.exp(exactMcNemarLogPValue(referenceOnly, candidateOnly));
}

function pairedComparison(referenceValues, candidateValues) {
  let bothPass = 0;
  let bothFail = 0;
  let referenceOnly = 0;
  let candidateOnly = 0;
  for (let index = 0; index < referenceValues.length; index += 1) {
    const reference = referenceValues[index] === true;
    const candidate = candidateValues[index] === true;
    if (reference && candidate) bothPass += 1;
    else if (reference) referenceOnly += 1;
    else if (candidate) candidateOnly += 1;
    else bothFail += 1;
  }
  const exactMcNemarLogP = exactMcNemarLogPValue(referenceOnly, candidateOnly);
  const exactMcNemarP = Math.exp(exactMcNemarLogP);
  return {
    bothPass,
    bothFail,
    referenceOnly,
    candidateOnly,
    discordant: referenceOnly + candidateOnly,
    exactMcNemarP,
    exactMcNemarLogP,
    exactMcNemarLog10P: exactMcNemarLogP / Math.log(10),
    exactMcNemarPUnderflow: exactMcNemarP === 0 && exactMcNemarLogP < 0,
  };
}

function indexGroups(groups, label) {
  const indexed = new Map();
  for (const group of requireGroups(groups, label)) {
    const taskId = requireString(group?.taskId, `${label}.taskId`);
    if (indexed.has(taskId)) throw new Error(`${label} repeats task ${taskId}.`);
    if (!Array.isArray(group.samples) || group.samples.length < 2) {
      throw new Error(`${label} task ${taskId} must contain at least two samples.`);
    }
    indexed.set(taskId, group);
  }
  return indexed;
}

export function compareVerifiedWgslRollouts(referenceGroups, candidateGroups) {
  const referenceByTask = indexGroups(referenceGroups, 'reference groups');
  const candidateByTask = indexGroups(candidateGroups, 'candidate groups');
  if (referenceByTask.size !== candidateByTask.size) {
    throw new Error('Reference and candidate rollout task counts differ.');
  }
  const paired = [];
  for (const [taskId, reference] of referenceByTask.entries()) {
    const candidate = candidateByTask.get(taskId);
    if (!candidate) throw new Error(`Candidate rollouts are missing task ${taskId}.`);
    if (reference.datasetHash !== candidate.datasetHash) {
      throw new Error(`Dataset hash differs for task ${taskId}.`);
    }
    if (reference.samples.length !== candidate.samples.length) {
      throw new Error(`Group size differs for task ${taskId}.`);
    }
    if (stableJson(reference.sampling) !== stableJson(candidate.sampling)) {
      throw new Error(`Sampling contract differs for task ${taskId}.`);
    }
    if (reference.verifierBundleHash !== candidate.verifierBundleHash) {
      throw new Error(`Verifier bundle hash differs for task ${taskId}.`);
    }
    if (reference.runtimeHash !== candidate.runtimeHash) {
      throw new Error(`Verifier runtime hash differs for task ${taskId}.`);
    }
    paired.push({ reference, candidate });
  }
  const firstReference = paired[0].reference;
  const firstCandidate = paired[0].candidate;
  const datasetHash = requireHash(firstReference.datasetHash, 'datasetHash');
  const referencePolicyHash = requireHash(firstReference.policyHash, 'referencePolicyHash');
  const candidatePolicyHash = requireHash(firstCandidate.policyHash, 'candidatePolicyHash');
  const anchorPolicyHash = requireHash(
    firstReference.referencePolicyHash,
    'anchorPolicyHash'
  );
  const verifierBundleHash = requireHash(
    firstReference.verifierBundleHash,
    'verifierBundleHash'
  );
  const runtimeHash = requireHash(firstReference.runtimeHash, 'runtimeHash');
  for (const { reference, candidate } of paired) {
    if (reference.datasetHash !== datasetHash || candidate.datasetHash !== datasetHash) {
      throw new Error('Rollout groups contain more than one dataset hash.');
    }
    if (reference.policyHash !== referencePolicyHash) {
      throw new Error('Reference rollout groups contain more than one policy hash.');
    }
    if (reference.referencePolicyHash !== anchorPolicyHash) {
      throw new Error(`Reference task ${reference.taskId} names a different anchor policy.`);
    }
    if (candidate.policyHash !== candidatePolicyHash) {
      throw new Error('Candidate rollout groups contain more than one policy hash.');
    }
    if (candidate.referencePolicyHash !== anchorPolicyHash) {
      throw new Error(`Candidate task ${candidate.taskId} names a different anchor policy.`);
    }
    if (reference.verifierBundleHash !== verifierBundleHash
        || candidate.verifierBundleHash !== verifierBundleHash) {
      throw new Error('Rollout groups contain more than one verifier bundle hash.');
    }
    if (reference.runtimeHash !== runtimeHash || candidate.runtimeHash !== runtimeHash) {
      throw new Error('Rollout groups contain more than one verifier runtime hash.');
    }
  }
  const reference = summarize(paired.map((entry) => entry.reference));
  const candidate = summarize(paired.map((entry) => entry.candidate));
  const referenceSamples = paired.flatMap((entry) => entry.reference.samples.map(samplePassed));
  const candidateSamples = paired.flatMap((entry) => entry.candidate.samples.map(samplePassed));
  const passAt1 = pairedComparison(
    paired.map((entry) => samplePassed(entry.reference.samples[0])),
    paired.map((entry) => samplePassed(entry.candidate.samples[0]))
  );
  const passAtK = pairedComparison(
    paired.map((entry) => entry.reference.samples.some(samplePassed)),
    paired.map((entry) => entry.candidate.samples.some(samplePassed))
  );
  return {
    artifactType: 'wgsl_rollout_comparison',
    schemaVersion: 1,
    datasetHash,
    referencePolicyHash,
    candidatePolicyHash,
    anchorPolicyHash,
    verifierBundleHash,
    runtimeHash,
    sampling: firstReference.sampling,
    reference,
    candidate,
    effects: {
      samplePassRate: candidate.samplePassRate - reference.samplePassRate,
      passAt1: candidate.passAt1 - reference.passAt1,
      passAtK: candidate.passAtK - reference.passAtK,
    },
    paired: {
      samples: pairedComparison(referenceSamples, candidateSamples),
      passAt1,
      passAtK,
    },
    claimBoundary: 'Family-disjoint public diagnostic only; not sealed promotion evidence.',
  };
}
