import { Tape } from './autodiff.mjs';
import { addBudget, counter } from './observation.mjs';
import {
  PARAM_COUNT,
  applyNeuralRuleTape,
  emitBehavioralTranscript,
  normal,
  rng,
  step,
} from './operator.mjs';

export const FAMILIES = ['twisted_huber_valley', 'anisotropic_gated_mlp'];

export function mean(values) {
  if (!Array.isArray(values) || values.length === 0) throw new Error('Empty array in mean');
  let sum = 0;
  for (let i = 0; i < values.length; i += 1) sum += values[i];
  return sum / values.length;
}

// Fresh zero-mean non-convex tasks: storing a constant parameter vector provides zero cross-task benefit.
export function sampleTasks(family, seed, count) {
  if (!FAMILIES.includes(family)) throw new Error(`Unsupported task family: ${family}`);
  const r = rng(seed);

  if (family === 'twisted_huber_valley') {
    const D = 12;
    return Array.from({ length: count }, (_, idx) => {
      const a = Array.from({ length: D }, () => (r() * 2 - 1) * 1.1);
      const w0 = Array.from({ length: D }, () => (r() * 2 - 1) * 0.8);
      const stiff = 35 + r() * 30;
      const curve = 1.3 + r() * 0.6;
      const invP = 1 / (D / 2);
      return {
        id: `task/${family}/${seed}/${idx}`,
        family,
        dimension: D,
        initial: w0,
        lossAndGradPlain(w) {
          let L = 0;
          const g = new Array(D).fill(0);
          for (let p = 0; p < D / 2; p += 1) {
            const i = 2 * p;
            const j = 2 * p + 1;
            const u = w[i] - a[i];
            const v = w[j] - a[j] - curve * u * u;
            const sq = Math.sqrt(1 + 4 * u * u);
            const hubU = sq - 1;
            const gHubU = (4 * u) / sq;
            L += (0.5 * hubU + 0.5 * stiff * v * v) * invP;
            g[i] = (0.5 * gHubU - 2 * curve * u * stiff * v) * invP;
            g[j] = stiff * v * invP;
          }
          return { loss: L, grad: g };
        },
        lossAndGradTape(tape, wIds) {
          let L = tape.const(0);
          const gIds = new Array(D);
          for (let p = 0; p < D / 2; p += 1) {
            const i = 2 * p;
            const j = 2 * p + 1;
            const u = tape.addConst(wIds[i], -a[i]);
            const u2 = tape.mul(u, u);
            const v = tape.sub(tape.addConst(wIds[j], -a[j]), tape.scale(u2, curve));
            const v2 = tape.mul(v, v);
            const sq = tape.sqrt(tape.addConst(tape.scale(u2, 4), 1));
            const hubU = tape.addConst(sq, -1);
            const gHubU = tape.div(tape.scale(u, 4), sq);
            L = tape.add(L, tape.add(tape.scale(hubU, 0.5 * invP), tape.scale(v2, 0.5 * stiff * invP)));
            gIds[i] = tape.scale(tape.sub(tape.scale(gHubU, 0.5), tape.scale(tape.mul(u, v), 2 * curve * stiff)), invP);
            gIds[j] = tape.scale(v, stiff * invP);
          }
          return { lossId: L, gradIds: gIds };
        },
      };
    });
  }

  // anisotropic_gated_mlp: 16D two-row gated bilinear neural predictor y = tanh(w1^T x) * (w2^T x)
  const Bw = 8;
  const D = 16;
  return Array.from({ length: count }, (_, idx) => {
    const t1 = Array.from({ length: Bw }, () => normal(r) * 0.9);
    const t2 = Array.from({ length: Bw }, () => normal(r) * 0.9);
    const scales = Array.from({ length: Bw }, (_, i) => (i < 2 ? 4.5 : 0.6));
    const exs = Array.from({ length: 16 }, () => {
      const x = Array.from({ length: Bw }, (_, i) => normal(r) * scales[i]);
      let d1 = 0;
      let d2 = 0;
      for (let i = 0; i < Bw; i += 1) {
        d1 += t1[i] * x[i];
        d2 += t2[i] * x[i];
      }
      return { x, y: Math.tanh(d1) * d2 };
    });
    const w0 = Array.from({ length: D }, () => (r() * 2 - 1) * 0.4);
    const invN = 1 / exs.length;

    return {
      id: `task/${family}/${seed}/${idx}`,
      family,
      dimension: D,
      initial: w0,
      lossAndGradPlain(w) {
        let L = 0.005 * w.reduce((s, v) => s + v * v, 0);
        const g = w.map(v => 0.01 * v);
        for (const ex of exs) {
          let d1 = 0;
          let d2 = 0;
          for (let i = 0; i < Bw; i += 1) {
            d1 += w[i] * ex.x[i];
            d2 += w[Bw + i] * ex.x[i];
          }
          const th = Math.tanh(d1);
          const err = th * d2 - ex.y;
          L += 0.5 * err * err * invN;
          const g1 = err * d2 * (1 - th * th) * invN;
          const g2 = err * th * invN;
          for (let i = 0; i < Bw; i += 1) {
            g[i] += g1 * ex.x[i];
            g[Bw + i] += g2 * ex.x[i];
          }
        }
        return { loss: L, grad: g };
      },
      lossAndGradTape(tape, wIds) {
        let wSq = tape.const(0);
        for (let i = 0; i < D; i += 1) wSq = tape.add(wSq, tape.mul(wIds[i], wIds[i]));
        let L = tape.scale(wSq, 0.005);
        const gIds = wIds.map(id => tape.scale(id, 0.01));
        for (const ex of exs) {
          let d1 = tape.const(0);
          let d2 = tape.const(0);
          for (let i = 0; i < Bw; i += 1) {
            d1 = tape.add(d1, tape.scale(wIds[i], ex.x[i]));
            d2 = tape.add(d2, tape.scale(wIds[Bw + i], ex.x[i]));
          }
          const th = tape.tanh(d1);
          const err = tape.addConst(tape.mul(th, d2), -ex.y);
          L = tape.add(L, tape.scale(tape.mul(err, err), 0.5 * invN));
          const omTh2 = tape.addConst(tape.scale(tape.mul(th, th), -1), 1);
          const g1 = tape.scale(tape.mul(err, tape.mul(d2, omTh2)), invN);
          const g2 = tape.scale(tape.mul(err, th), invN);
          for (let i = 0; i < Bw; i += 1) {
            gIds[i] = tape.add(gIds[i], tape.scale(g1, ex.x[i]));
            gIds[Bw + i] = tape.add(gIds[Bw + i], tape.scale(g2, ex.x[i]));
          }
        }
        return { lossId: L, gradIds: gIds };
      },
    };
  });
}

// Fresh downstream task evaluation always starts with empty episode state (history = null).
export function evaluateRule(phi, rule, tasks, innerSteps, budget) {
  const losses = new Array(tasks.length);
  for (let ti = 0; ti < tasks.length; ti += 1) {
    const task = tasks[ti];
    let state = { theta: [...task.initial], history: null };
    for (let s = 0; s < innerSteps; s += 1) {
      state = step({
        theta: state.theta,
        phi,
        rule,
        method: 'learned',
        objectiveId: task.id,
        lossAndGrad: w => task.lossAndGradPlain(w),
        stepIndex: s,
        history: state.history,
      }, budget);
    }
    budget.oracleCalls += 1;
    losses[ti] = task.lossAndGradPlain(state.theta).loss;
  }
  return losses;
}

// Differentiable unrolled meta-loss + meta-gradient wrt candidatePhi across supportTasks.
export function metaLossAndGrad(candidatePhi, rule, supportTasks, innerSteps, innerBudget) {
  const tape = new Tape();
  const phiIds = candidatePhi.map(x => tape.var(x));
  let totalLoss = tape.const(0);
  const invT = 1 / supportTasks.length;

  for (const task of supportTasks) {
    let stateIds = null;
    let thetaIds = task.initial.map(x => tape.const(x));
    for (let s = 0; s < innerSteps; s += 1) {
      const { lossId, gradIds } = task.lossAndGradTape(tape, thetaIds);
      innerBudget.oracleCalls += 1;
      innerBudget.updates += 1;
      const out = applyNeuralRuleTape(tape, thetaIds, lossId, gradIds, phiIds, rule, s, stateIds);
      thetaIds = out.thetaIds;
      stateIds = out.stateIds;
    }
    const { lossId: termLoss } = task.lossAndGradTape(tape, thetaIds);
    innerBudget.oracleCalls += 1;
    totalLoss = tape.add(totalLoss, tape.scale(termLoss, invT));
  }
  tape.backward(totalLoss);
  return {
    loss: tape.nodes[totalLoss].val,
    grad: phiIds.map(id => tape.nodes[id].grad),
  };
}

// Execute one meta-proposal episode (metaSteps sequential updates of targetPhi).
export function proposeSuccessor({
  targetPhi,
  proposerPhi,
  rule,
  arm,
  supportTasks,
  innerSteps,
  metaSteps,
  metaObjectiveId,
  initialHistory = null,
  settings = {},
  emitTranscript = false,
  transcriptProbes = 24,
  transcriptSeed = 424242,
}, budget) {
  const outerBudget = counter();
  const innerBudget = counter();

  if (arm === 'serialization_only') {
    return {
      theta: [...targetPhi],
      history: initialHistory ? structuredClone(initialHistory) : null,
      transcript: null,
      outerBudget,
      innerBudget,
    };
  }

  const isConventional = arm.startsWith('tuned_') || arm.startsWith('paired_sgd')
    || arm.startsWith('paired_adam') || arm.startsWith('paired_bfgs');
  const method = isConventional ? settings.method : 'learned';

  let state = {
    theta: [...targetPhi],
    history: initialHistory ? structuredClone(initialHistory) : null,
  };

  for (let s = 0; s < metaSteps; s += 1) {
    state = step({
      theta: state.theta,
      phi: proposerPhi,
      rule,
      method,
      rate: settings.rate ?? 0.05,
      beta: settings.beta ?? 0.8,
      objectiveId: metaObjectiveId,
      lossAndGrad: candPhi => metaLossAndGrad(candPhi, rule, supportTasks, innerSteps, innerBudget),
      stepIndex: s,
      history: state.history,
    }, outerBudget);
  }

  let transcript = null;
  if (emitTranscript) {
    transcript = emitBehavioralTranscript(state.theta, rule, transcriptProbes, transcriptSeed);
    outerBudget.regenerationCalls += transcriptProbes;
  }

  addBudget(budget, outerBudget);
  addBudget(budget, innerBudget);
  return {
    theta: state.theta,
    history: state.history,
    transcript,
    outerBudget,
    innerBudget,
  };
}

// Strictly matched preprocessing: 9 self-target initial rule candidates vs 9 candidates per conventional optimizer
// on fresh training/calibration task populations (never touching selection holdout or confirmation populations).
export function initializeAndCalibrate({ seed, family, rule, config }) {
  const {
    trainingCandidates = 9,
    trainingEnvironments = 2,
    trainSupportCount = 6,
    trainQueryCount = 8,
    trainInnerSteps = 7,
    trainMetaSteps = 6,
    sgdGrid,
    adamGrid,
    bfgsRates,
  } = config;

  if (sgdGrid.length !== trainingCandidates
      || adamGrid.length !== trainingCandidates
      || bfgsRates.length !== trainingCandidates) {
    throw new Error('Candidate counts across learned initializer and all conventional calibrators must match');
  }

  const randInit = rng(seed + 17);
  const initSupport = Array.from({ length: trainingEnvironments }, (_, i) => sampleTasks(family, seed + 100 + i * 31, trainSupportCount));
  const initQuery = Array.from({ length: trainingEnvironments }, (_, i) => sampleTasks(family, seed + 200 + i * 31, trainQueryCount));

  const learnedBudget = counter();
  let bestLearned = null;

  for (let k = 0; k < trainingCandidates; k += 1) {
    const candPhi = Array.from({ length: PARAM_COUNT }, (_, idx) => {
      if (idx === 45) return -1.8 + (randInit() - 0.5) * 0.4;
      if (idx === 46) return -2.2 + (randInit() - 0.5) * 0.4;
      if (idx === 47) return -1.8 + (randInit() - 0.5) * 0.4;
      return normal(randInit) * 0.12;
    });
    const queryLosses = initSupport.map((sup, ei) => {
      const prop = proposeSuccessor({
        targetPhi: candPhi,
        proposerPhi: candPhi,
        rule,
        arm: 'evolving_ser_reset',
        supportTasks: sup,
        innerSteps: trainInnerSteps,
        metaSteps: trainMetaSteps,
        metaObjectiveId: `init/${seed}/${family}/${k}/${ei}`,
        initialHistory: null,
      }, learnedBudget);
      return mean(evaluateRule(prop.theta, rule, initQuery[ei], trainInnerSteps, learnedBudget));
    });
    const fitness = mean(queryLosses);
    const entry = { candidate: k, phi: candPhi, queryLosses, fitness };
    if (!bestLearned || fitness < bestLearned.fitness) bestLearned = entry;
  }

  const calSupport = Array.from({ length: trainingEnvironments }, (_, i) => sampleTasks(family, seed + 400 + i * 31, trainSupportCount));
  const calQuery = Array.from({ length: trainingEnvironments }, (_, i) => sampleTasks(family, seed + 500 + i * 31, trainQueryCount));

  const conventionalSpecs = {
    sgd: sgdGrid.map(([rate, beta]) => ({ method: 'sgd', rate, beta })),
    adam: adamGrid.map(([rate, beta]) => ({ method: 'adam', rate, beta })),
    bfgs: bfgsRates.map(rate => ({ method: 'bfgs', rate, beta: 0 })),
  };

  const calibrations = {};
  for (const [method, grid] of Object.entries(conventionalSpecs)) {
    const calBudget = counter();
    const rows = [];
    let best = null;
    for (let k = 0; k < grid.length; k += 1) {
      const spec = grid[k];
      const queryLosses = calSupport.map((sup, ei) => {
        const prop = proposeSuccessor({
          targetPhi: bestLearned.phi,
          proposerPhi: bestLearned.phi,
          rule,
          arm: `tuned_${method}`,
          supportTasks: sup,
          innerSteps: trainInnerSteps,
          metaSteps: trainMetaSteps,
          metaObjectiveId: `cal/${method}/${seed}/${family}/${k}/${ei}`,
          initialHistory: null,
          settings: spec,
        }, calBudget);
        return mean(evaluateRule(prop.theta, rule, calQuery[ei], trainInnerSteps, calBudget));
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
    sharedChargedOracleCalls: learnedBudget.oracleCalls
      + calibrations.sgd.budget.oracleCalls
      + calibrations.adam.budget.oracleCalls
      + calibrations.bfgs.budget.oracleCalls,
  };
}
