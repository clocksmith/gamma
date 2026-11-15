import {
  BLOCK_WIDTH,
  PARAM_COUNT,
  counter,
  decodePhi,
  dot,
  normal,
  orthonormalize,
  rng,
  step,
} from './operator.mjs';

export const FAMILIES = ['subspace_logistic', 'gated_bilinear'];

export function mean(values) {
  if (!Array.isArray(values) || values.length === 0) throw new Error('Empty array in mean');
  let sum = 0;
  for (let i = 0; i < values.length; i += 1) sum += values[i];
  return sum / values.length;
}

// Construct an environment with an unknown latent 2D active subspace U_env in R^16.
// U_env is private to task construction and post-hoc mechanistic diagnostics; never passed to updaters.
export function makeEnvironment(seed) {
  const B = BLOCK_WIDTH;
  const rand = rng(seed);
  const raw = [
    Array.from({ length: B }, () => normal(rand)),
    Array.from({ length: B }, () => normal(rand)),
  ];
  const Uenv = orthonormalize(raw, B, seed + 13, 2);
  return { seed, blockWidth: B, subspaceRank: 2, Uenv };
}

export function subspaceOverlap(phi, rule, env) {
  const { U2 } = decodePhi(phi, rule);
  let sumSq = 0;
  for (let i = 0; i < 2; i += 1) {
    for (let j = 0; j < 2; j += 1) {
      const p = dot(U2[i], env.Uenv[j]);
      sumSq += p * p;
    }
  }
  return sumSq / 2;
}

export function sampleTasks(env, seed, count, family) {
  if (!FAMILIES.includes(family)) throw new Error(`Unsupported task family: ${family}`);
  const B = env.blockWidth;
  const { Uenv } = env;
  const rand = rng(seed);

  return Array.from({ length: count }, (_, idx) => {
    if (family === 'subspace_logistic') {
      // 1x16 convex binary classification: full isotropic unit-variance distractors across all 16 coords,
      // true boundary wTrue in span(U_env).
      const z0 = normal(rand) * 2.4;
      const z1 = normal(rand) * 2.4;
      const wTrue = Array.from({ length: B }, (_, b) => Uenv[0][b] * z0 + Uenv[1][b] * z1);
      const examples = Array.from({ length: 24 }, () => {
        const x = Array.from({ length: B }, () => normal(rand));
        const y = dot(x, wTrue) >= 0 ? 1 : -1;
        return { x, y };
      });
      const initial = Array.from({ length: B }, () => (rand() * 2 - 1) * 0.25);
      return {
        id: `task/${env.seed}/${seed}/${family}/${idx}`,
        family,
        dimension: B,
        initial,
        loss(w) {
          let sum = 0;
          for (let n = 0; n < examples.length; n += 1) {
            const ex = examples[n];
            const margin = -ex.y * dot(ex.x, w);
            sum += Math.max(margin, 0) + Math.log1p(Math.exp(-Math.abs(margin)));
          }
          return sum / examples.length + 0.015 * dot(w, w);
        },
      };
    }

    // gated_bilinear: 2x16 = 32D non-convex two-row predictor y = tanh(w1^T x) * (w2^T x)
    // Inputs have signal variance along U_env plus isotropic distractors across all 16 coords.
    const a0 = (rand() < 0.5 ? -1 : 1) * (1.2 + 0.6 * rand());
    const a1 = (rand() * 2 - 1) * 0.8;
    const b0 = (rand() * 2 - 1) * 0.8;
    const b1 = (rand() < 0.5 ? -1 : 1) * (1.2 + 0.6 * rand());
    const t1 = Array.from({ length: B }, (_, b) => a0 * Uenv[0][b] + a1 * Uenv[1][b]);
    const t2 = Array.from({ length: B }, (_, b) => b0 * Uenv[0][b] + b1 * Uenv[1][b]);
    const examples = Array.from({ length: 24 }, () => {
      const s0 = normal(rand) * 1.4;
      const s1 = normal(rand) * 1.4;
      const x = Array.from({ length: B }, (_, b) => Uenv[0][b] * s0 + Uenv[1][b] * s1 + 0.55 * normal(rand));
      const y = Math.tanh(dot(t1, x)) * dot(t2, x);
      return { x, y };
    });
    const initial = Array.from({ length: 2 * B }, () => (rand() * 2 - 1) * 0.25);
    return {
      id: `task/${env.seed}/${seed}/${family}/${idx}`,
      family,
      dimension: 2 * B,
      initial,
      loss(w) {
        let sum = 0;
        for (let n = 0; n < examples.length; n += 1) {
          const ex = examples[n];
          let dot1 = 0;
          let dot2 = 0;
          for (let b = 0; b < B; b += 1) {
            dot1 += w[b] * ex.x[b];
            dot2 += w[B + b] * ex.x[b];
          }
          const pred = Math.tanh(dot1) * dot2;
          const err = pred - ex.y;
          sum += 0.5 * err * err;
        }
        return sum / examples.length + 0.005 * dot(w, w);
      },
    };
  });
}

// Fresh downstream task evaluation always starts with empty episode state (history = null).
export function evaluateRule(phi, rule, tasks, innerSteps, probeBaseSeed, budget) {
  const decoded = decodePhi(phi, rule);
  const losses = new Array(tasks.length);
  for (let ti = 0; ti < tasks.length; ti += 1) {
    const task = tasks[ti];
    let state = { theta: [...task.initial], history: null };
    for (let s = 0; s < innerSteps; s += 1) {
      state = step({
        theta: state.theta,
        phi,
        decoded,
        rule,
        method: 'learned',
        objectiveId: task.id,
        loss: task.loss,
        probeSeed: probeBaseSeed + ti * 97 + s,
        stepIndex: s,
        history: state.history,
      }, budget);
    }
    budget.scalarQueries += 1;
    losses[ti] = task.loss(state.theta);
  }
  return losses;
}

// Execute one meta-proposal episode (metaSteps sequential 8-query updates of targetPhi).
export function proposeSuccessor({
  targetPhi,
  proposerPhi,
  rule,
  arm,
  supportTasks,
  innerSteps,
  metaSteps,
  metaObjectiveId,
  probeBaseSeed,
  innerProbeSeed,
  initialHistory = null,
  settings = {},
}, budget) {
  const outerBudget = counter();
  const innerBudget = counter();

  if (arm === 'serialization_only') {
    return {
      theta: [...targetPhi],
      history: initialHistory ? structuredClone(initialHistory) : null,
      outerBudget,
      innerBudget,
    };
  }

  const isConventional = arm.startsWith('tuned_') || arm.startsWith('paired_spsa')
    || arm.startsWith('paired_adam') || arm.startsWith('paired_bfgs');
  const method = isConventional ? settings.method : 'learned';
  const decodedProposer = method === 'learned' ? decodePhi(proposerPhi, rule) : null;

  let state = {
    theta: [...targetPhi],
    history: initialHistory ? structuredClone(initialHistory) : null,
  };

  const metaLoss = candidatePhi => mean(
    evaluateRule(candidatePhi, rule, supportTasks, innerSteps, innerProbeSeed, innerBudget),
  );

  for (let s = 0; s < metaSteps; s += 1) {
    state = step({
      theta: state.theta,
      phi: proposerPhi,
      decoded: decodedProposer,
      rule,
      method,
      rate: settings.rate ?? 0.1,
      beta: settings.beta ?? 0.9,
      radius: settings.radius ?? 0.005,
      objectiveId: metaObjectiveId,
      loss: metaLoss,
      probeSeed: probeBaseSeed + s,
      stepIndex: s,
      history: state.history,
    }, outerBudget);
  }

  budget.scalarQueries += outerBudget.scalarQueries + innerBudget.scalarQueries;
  budget.updates += outerBudget.updates + innerBudget.updates;
  budget.skippedCurvature += outerBudget.skippedCurvature + innerBudget.skippedCurvature;
  budget.clamps += outerBudget.clamps + innerBudget.clamps;
  budget.peakStateBytes = Math.max(budget.peakStateBytes, outerBudget.peakStateBytes, innerBudget.peakStateBytes);

  return {
    theta: state.theta,
    history: state.history,
    outerBudget,
    innerBudget,
  };
}

// Strictly matched preprocessing: 9 self-target initial rule candidates vs 9 candidates per conventional method
// across independent pretraining/calibration environments (never touching evaluation environments).
export function initializeAndCalibrate({ seed, family, rule, config }) {
  const {
    trainingCandidates = 9,
    trainingEnvironments = 2,
    trainSupportCount = 4,
    trainQueryCount = 4,
    trainInnerSteps = 8,
    trainMetaSteps = 9,
    spsaRates,
    adamGrid,
    bfgsRates,
  } = config;

  if (spsaRates.length !== trainingCandidates
      || adamGrid.length !== trainingCandidates
      || bfgsRates.length !== trainingCandidates) {
    throw new Error('Candidate counts across learned initializer and all conventional calibrators must match exactly');
  }

  const randInit = rng(seed + 11);
  const initEnvs = Array.from({ length: trainingEnvironments }, (_, i) => makeEnvironment(seed + 100 + i * 17));
  const initSupport = initEnvs.map((env, i) => sampleTasks(env, seed + 200 + i * 17, trainSupportCount, family));
  const initQuery = initEnvs.map((env, i) => sampleTasks(env, seed + 300 + i * 17, trainQueryCount, family));

  const learnedBudget = counter();
  const learnedCandidates = [];
  let bestLearned = null;

  for (let k = 0; k < trainingCandidates; k += 1) {
    // Unaligned small random subspace vectors + diverse dynamical policy draws
    const candPhi = Array.from({ length: PARAM_COUNT }, (_, idx) => (
      idx < 2 * BLOCK_WIDTH ? normal(randInit) * 0.15 : (randInit() * 2 - 1) * 0.9 - (idx === 2 * BLOCK_WIDTH ? 0.8 : 0)
    ));
    const queryLosses = initEnvs.map((env, ei) => {
      const prop = proposeSuccessor({
        targetPhi: candPhi,
        proposerPhi: candPhi,
        rule,
        arm: 'hereditary_reset',
        supportTasks: initSupport[ei],
        innerSteps: trainInnerSteps,
        metaSteps: trainMetaSteps,
        metaObjectiveId: `init/${seed}/${family}/${k}/${ei}`,
        probeBaseSeed: seed + 1000 + k * 100 + ei * 20,
        innerProbeSeed: seed + 5000,
        initialHistory: null,
      }, learnedBudget);
      return mean(evaluateRule(prop.theta, rule, initQuery[ei], trainInnerSteps, seed + 6000, learnedBudget));
    });
    const fitness = mean(queryLosses);
    const entry = { candidate: k, phi: candPhi, queryLosses, fitness };
    learnedCandidates.push(entry);
    if (!bestLearned || fitness < bestLearned.fitness) bestLearned = entry;
  }

  // Separate calibration environments for conventional meta-optimizers, exact same dimensions and step counts
  const calEnvs = Array.from({ length: trainingEnvironments }, (_, i) => makeEnvironment(seed + 400 + i * 17));
  const calSupport = calEnvs.map((env, i) => sampleTasks(env, seed + 500 + i * 17, trainSupportCount, family));
  const calQuery = calEnvs.map((env, i) => sampleTasks(env, seed + 600 + i * 17, trainQueryCount, family));

  const conventionalSpecs = {
    spsa: spsaRates.map(rate => ({ method: 'spsa', rate, beta: 0, radius: 0.005 })),
    adam: adamGrid.map(([rate, beta]) => ({ method: 'adam', rate, beta, radius: 0.005 })),
    bfgs: bfgsRates.map(rate => ({ method: 'bfgs', rate, beta: 0, radius: 0.005 })),
  };

  const calibrations = {};
  for (const [method, grid] of Object.entries(conventionalSpecs)) {
    const calBudget = counter();
    const rows = [];
    let best = null;
    for (let k = 0; k < grid.length; k += 1) {
      const spec = grid[k];
      const queryLosses = calEnvs.map((_, ei) => {
        const prop = proposeSuccessor({
          targetPhi: bestLearned.phi,
          proposerPhi: bestLearned.phi,
          rule,
          arm: `tuned_${method}`,
          supportTasks: calSupport[ei],
          innerSteps: trainInnerSteps,
          metaSteps: trainMetaSteps,
          metaObjectiveId: `cal/${method}/${seed}/${family}/${k}/${ei}`,
          probeBaseSeed: seed + 2000 + k * 100 + ei * 20,
          innerProbeSeed: seed + 7000,
          initialHistory: null,
          settings: spec,
        }, calBudget);
        return mean(evaluateRule(prop.theta, rule, calQuery[ei], trainInnerSteps, seed + 8000, calBudget));
      });
      const fitness = mean(queryLosses);
      const row = { candidate: k, ...spec, queryLosses, fitness };
      rows.push(row);
      if (!best || fitness < best.fitness) best = row;
    }
    calibrations[method] = { selected: best, candidates: rows, budget: calBudget };
  }

  return {
    initialPhi: bestLearned.phi,
    selectedCandidate: bestLearned.candidate,
    initialFitness: bestLearned.fitness,
    learnedBudget,
    calibrations,
    sharedChargedScalarQueries: learnedBudget.scalarQueries
      + calibrations.spsa.budget.scalarQueries
      + calibrations.adam.budget.scalarQueries
      + calibrations.bfgs.budget.scalarQueries,
  };
}
