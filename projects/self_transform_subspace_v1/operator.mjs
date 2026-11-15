import { createHash } from 'node:crypto';
import { observationWindow } from './observation.mjs';

export const BLOCK_WIDTH = 16;
export const RULE_BLOCKS = 3;
export const PARAM_COUNT = RULE_BLOCKS * BLOCK_WIDTH; // 48 float64 weights
export const SCHEMA = 'gamma.self-transform-subspace/v1';

export const CANDIDATE_RULES = [
  'block_subspace_2mode',
  'block_subspace_1mode',
  'kronecker_subspace_2mode',
  'isotropic_homog_ablation',
];

export function rng(seed) {
  let state = seed >>> 0;
  return () => {
    state = (Math.imul(state, 1664525) + 1013904223) >>> 0;
    return state / 4294967296;
  };
}

export function normal(rand) {
  const u1 = Math.max(1e-12, rand());
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * rand());
}

export function dot(a, b) {
  let s = 0;
  for (let i = 0; i < a.length; i += 1) s += a[i] * b[i];
  return s;
}

export function norm(a) {
  return Math.sqrt(dot(a, a));
}

export function clamp(x, lo, hi) {
  return Math.max(lo, Math.min(hi, x));
}

function sigmoid(z) {
  return 1 / (1 + Math.exp(-clamp(z, -20, 20)));
}

export function checkVector(vec, expectedLength = vec?.length) {
  if (!Array.isArray(vec) || vec.length !== expectedLength || expectedLength < 1 || !vec.every(Number.isFinite)) {
    throw new Error(`Expected finite vector of length ${expectedLength}`);
  }
  return vec;
}

export function counter() {
  return {
    scalarQueries: 0,
    updates: 0,
    skippedCurvature: 0,
    clamps: 0,
    peakStateBytes: 0,
  };
}

export function addBudget(target, delta) {
  target.scalarQueries += delta.scalarQueries;
  target.updates += delta.updates;
  target.skippedCurvature += delta.skippedCurvature;
  target.clamps += delta.clamps;
  target.peakStateBytes = Math.max(target.peakStateBytes, delta.peakStateBytes);
  return target;
}

export function sha256(text) {
  return createHash('sha256').update(text).digest('hex');
}

export function orthonormalize(vectors, dim, fallbackSeed = 97, count = vectors.length) {
  const basis = [];
  for (const raw of vectors) {
    if (basis.length >= count) break;
    const v = [...raw];
    for (const u of basis) {
      const p = dot(v, u);
      for (let i = 0; i < dim; i += 1) v[i] -= p * u[i];
    }
    const n = norm(v);
    if (n > 1e-9) basis.push(v.map(x => x / n));
  }
  const rand = rng(fallbackSeed);
  while (basis.length < count) {
    const v = Array.from({ length: dim }, () => normal(rand));
    for (const u of basis) {
      const p = dot(v, u);
      for (let i = 0; i < dim; i += 1) v[i] -= p * u[i];
    }
    const n = norm(v);
    if (n > 1e-9) basis.push(v.map(x => x / n));
  }
  return basis;
}

// Decode Phi in R^48 = [v1 (16); v2 (16); c (16)] into orthonormal subspace frame + smooth dynamics.
export function decodePhi(phi, rule = 'block_subspace_2mode') {
  checkVector(phi, PARAM_COUNT);
  if (!CANDIDATE_RULES.includes(rule)) throw new Error(`Unknown candidate rule: ${rule}`);
  const B = BLOCK_WIDTH;
  const v1 = phi.slice(0, B);
  const v2 = phi.slice(B, 2 * B);
  const c = phi.slice(2 * B, 3 * B);
  const n1 = norm(v1);
  const n2 = norm(v2);
  const U2 = orthonormalize([v1, v2], B, 97, 2);

  const baseEta = 0.03 + 0.45 * sigmoid(c[0]);
  const activeBoost1 = 0.30 + 2.20 * sigmoid(c[1] + n1 - 0.6);
  const activeBoost2 = 0.30 + 2.20 * sigmoid(c[2] + n2 - 0.6);
  const orthoGain = 0.08 + 0.90 * sigmoid(c[3]);
  const rmsBeta = 0.80 + 0.18 * sigmoid(c[4]);
  const momBeta = 0.80 * sigmoid(c[5]);
  const stepDecay = 0.02 + 0.35 * sigmoid(c[6]);
  const relFloor = 0.05 + 0.45 * sigmoid(c[7]);
  const probeRadius = 1e-3 + 0.015 * sigmoid(c[8]);

  return {
    rule, U2, n1, n2, baseEta, activeBoost1, activeBoost2, orthoGain,
    rmsBeta, momBeta, stepDecay, relFloor, probeRadius,
  };
}

// Exact IEEE-754 float64 little-endian artifact serialization for rule parameters Phi.
export function serialize(phi, rule = 'block_subspace_2mode') {
  checkVector(phi, PARAM_COUNT);
  if (!CANDIDATE_RULES.includes(rule)) throw new Error(`Unsupported rule: ${rule}`);
  const bytes = Buffer.alloc(PARAM_COUNT * 8);
  for (let i = 0; i < PARAM_COUNT; i += 1) bytes.writeDoubleLE(phi[i], i * 8);
  const payload = { schema: SCHEMA, rule, weightsHex: bytes.toString('hex') };
  return JSON.stringify({ ...payload, sha256: sha256(JSON.stringify(payload)) });
}

export function reconstruct(text) {
  const parsed = JSON.parse(text);
  const keys = Object.keys(parsed).sort().join(',');
  if (keys !== 'rule,schema,sha256,weightsHex' || parsed.schema !== SCHEMA
      || !CANDIDATE_RULES.includes(parsed.rule)) {
    throw new Error('Invalid or unsupported rule artifact');
  }
  const hexLen = PARAM_COUNT * 16;
  if (typeof parsed.weightsHex !== 'string' || parsed.weightsHex.length !== hexLen
      || !/^[0-9a-f]+$/.test(parsed.weightsHex)) {
    throw new Error('Corrupt weight byte encoding');
  }
  const payload = { schema: parsed.schema, rule: parsed.rule, weightsHex: parsed.weightsHex };
  if (sha256(JSON.stringify(payload)) !== parsed.sha256) {
    throw new Error('Artifact SHA-256 mismatch');
  }
  const bytes = Buffer.from(parsed.weightsHex, 'hex');
  const phi = Array.from({ length: PARAM_COUNT }, (_, i) => bytes.readDoubleLE(i * 8));
  checkVector(phi, PARAM_COUNT);
  return { phi, rule: parsed.rule };
}

// Exact recursive float64 state serialization for retained-memory factorial arms.
export function freezeState(value) {
  const encNum = x => {
    if (!Number.isFinite(x)) throw new Error('Non-finite value in state artifact');
    const b = Buffer.alloc(8);
    b.writeDoubleLE(x, 0);
    return { f64: b.toString('hex') };
  };
  const encode = v => (typeof v === 'number' ? encNum(v)
    : Array.isArray(v) ? v.map(encode)
      : v && typeof v === 'object' ? Object.fromEntries(Object.entries(v).map(([k, val]) => [k, encode(val)])) : v);
  const payload = JSON.stringify(encode(value));
  return JSON.stringify({ schema: `${SCHEMA}-state`, payload, sha256: sha256(payload) });
}

export function restoreState(text) {
  const parsed = JSON.parse(text);
  if (parsed.schema !== `${SCHEMA}-state` || typeof parsed.payload !== 'string'
      || sha256(parsed.payload) !== parsed.sha256) {
    throw new Error('Invalid or corrupt state artifact');
  }
  const decNum = hex => {
    if (typeof hex !== 'string' || !/^[0-9a-f]{16}$/.test(hex)) throw new Error('Invalid float64 hex');
    const val = Buffer.from(hex, 'hex').readDoubleLE(0);
    if (!Number.isFinite(val)) throw new Error('Non-finite float64 in state artifact');
    return val;
  };
  const decode = v => (v && typeof v === 'object' && !Array.isArray(v)
    && Object.keys(v).length === 1 && typeof v.f64 === 'string'
    ? decNum(v.f64)
    : Array.isArray(v) ? v.map(decode)
      : v && typeof v === 'object' ? Object.fromEntries(Object.entries(v).map(([k, val]) => [k, decode(val)])) : v);
  return decode(JSON.parse(parsed.payload));
}

function numericScalarCount(v) {
  if (typeof v === 'number') return 1;
  if (Array.isArray(v)) return v.reduce((s, x) => s + numericScalarCount(x), 0);
  if (v && typeof v === 'object') return Object.values(v).reduce((s, x) => s + numericScalarCount(x), 0);
  return 0;
}

// Universal single-step update using observationWindow(limit=8).
// Identical code path updates task weights (M=1 or M=2) and self-parameters Phi (M=3).
export function step({
  theta,
  phi = null,
  decoded = null,
  rule = 'block_subspace_2mode',
  method = 'learned',
  rate = 0.1,
  beta = 0.9,
  radius = 0.005,
  objectiveId,
  loss,
  probeSeed,
  stepIndex = 0,
  history = null,
}, budget) {
  checkVector(theta);
  const D = theta.length;
  const window = observationWindow({ objectiveId, theta, previous: history, loss, limit: 8 });
  const prev = window.history;
  const rand = rng(probeSeed);

  let nextTheta;
  let nextHistory;

  if (method === 'learned') {
    const B = BLOCK_WIDTH;
    if (D % B !== 0) throw new Error(`Target dimension ${D} must be a multiple of block width ${B}`);
    const M = D / B;
    const cfg = decoded ?? decodePhi(phi, rule);
    const r = cfg.probeRadius;
    const gradEst = new Array(D).fill(0);
    const precondGrad = new Array(D).fill(0);

    if (cfg.rule === 'kronecker_subspace_2mode') {
      // Multi-block Kronecker probes across all M blocks simultaneously
      for (let k = 0; k < 4; k += 1) {
        const rowSigns = Array.from({ length: M }, () => (rand() < 0.5 ? -1 : 1));
        const d = new Array(D).fill(0);
        let modeGain;
        let scaleFactor;
        if (k === 0) {
          for (let m = 0; m < M; m += 1) {
            for (let b = 0; b < B; b += 1) d[m * B + b] = rowSigns[m] * cfg.U2[0][b];
          }
          modeGain = cfg.activeBoost1;
          scaleFactor = 1.0;
        } else if (k === 1) {
          for (let m = 0; m < M; m += 1) {
            for (let b = 0; b < B; b += 1) d[m * B + b] = rowSigns[m] * cfg.U2[1][b];
          }
          modeGain = cfg.activeBoost2;
          scaleFactor = 1.0;
        } else {
          const z = Array.from({ length: B }, () => (rand() < 0.5 ? -1 : 1));
          const p0 = dot(z, cfg.U2[0]);
          const p1 = dot(z, cfg.U2[1]);
          for (let m = 0; m < M; m += 1) {
            for (let b = 0; b < B; b += 1) {
              d[m * B + b] = rowSigns[m] * (z[b] - p0 * cfg.U2[0][b] - p1 * cfg.U2[1][b]);
            }
          }
          modeGain = cfg.orthoGain;
          scaleFactor = 0.5;
        }
        const ptPlus = new Array(D);
        const ptMinus = new Array(D);
        for (let i = 0; i < D; i += 1) {
          ptPlus[i] = theta[i] + r * d[i];
          ptMinus[i] = theta[i] - r * d[i];
        }
        const slope = (window.query(ptPlus) - window.query(ptMinus)) / (2 * r);
        for (let i = 0; i < D; i += 1) {
          const gi = scaleFactor * slope * d[i];
          gradEst[i] += gi;
          precondGrad[i] += modeGain * gi;
        }
      }
    } else {
      // Block-decoupled cyclic probing across the M blocks
      const compHits = new Array(M).fill(0);
      const isoHits = new Array(M).fill(0);
      const probeSpecs = [];
      for (let k = 0; k < 4; k += 1) {
        const m = (stepIndex * 4 + k) % M;
        let kind;
        if (cfg.rule === 'isotropic_homog_ablation') {
          kind = 'iso';
          isoHits[m] += 1;
        } else if (cfg.rule === 'block_subspace_1mode') {
          kind = k === 0 ? 'u0' : 'comp1';
          if (kind === 'comp1') compHits[m] += 1;
        } else {
          // block_subspace_2mode
          kind = k === 0 ? 'u0' : k === 1 ? 'u1' : 'comp2';
          if (kind === 'comp2') compHits[m] += 1;
        }
        probeSpecs.push({ m, kind });
      }

      for (const spec of probeSpecs) {
        const { m, kind } = spec;
        const offset = m * B;
        const d = new Array(D).fill(0);
        let modeGain;
        let scaleFactor;

        if (kind === 'u0') {
          for (let b = 0; b < B; b += 1) d[offset + b] = cfg.U2[0][b];
          modeGain = cfg.activeBoost1;
          scaleFactor = 1.0;
        } else if (kind === 'u1') {
          for (let b = 0; b < B; b += 1) d[offset + b] = cfg.U2[1][b];
          modeGain = cfg.activeBoost2;
          scaleFactor = 1.0;
        } else if (kind === 'comp1') {
          const z = Array.from({ length: B }, () => (rand() < 0.5 ? -1 : 1));
          const p0 = dot(z, cfg.U2[0]);
          for (let b = 0; b < B; b += 1) d[offset + b] = z[b] - p0 * cfg.U2[0][b];
          modeGain = cfg.orthoGain;
          scaleFactor = 1 / compHits[m];
        } else if (kind === 'comp2') {
          const z = Array.from({ length: B }, () => (rand() < 0.5 ? -1 : 1));
          const p0 = dot(z, cfg.U2[0]);
          const p1 = dot(z, cfg.U2[1]);
          for (let b = 0; b < B; b += 1) {
            d[offset + b] = z[b] - p0 * cfg.U2[0][b] - p1 * cfg.U2[1][b];
          }
          modeGain = cfg.orthoGain;
          scaleFactor = 1 / compHits[m];
        } else {
          // isotropic_homog_ablation
          for (let b = 0; b < B; b += 1) d[offset + b] = rand() < 0.5 ? -1 : 1;
          modeGain = 1.0;
          scaleFactor = 1 / isoHits[m];
        }

        const ptPlus = new Array(D);
        const ptMinus = new Array(D);
        for (let i = 0; i < D; i += 1) {
          ptPlus[i] = theta[i] + r * d[i];
          ptMinus[i] = theta[i] - r * d[i];
        }
        const slope = (window.query(ptPlus) - window.query(ptMinus)) / (2 * r);
        for (let b = 0; b < B; b += 1) {
          const gi = scaleFactor * slope * d[offset + b];
          gradEst[offset + b] += gi;
          precondGrad[offset + b] += modeGain * gi;
        }
      }
    }

    const t = (prev?.t ?? 0) + 1;
    const prevRms = prev?.blockRms ?? new Array(M).fill(0);
    const prevInitRms = prev?.initRms ?? new Array(M).fill(0);
    const prevTouches = prev?.touches ?? new Array(M).fill(0);
    const nextRms = [...prevRms];
    const nextInitRms = [...prevInitRms];
    const nextTouches = [...prevTouches];

    for (let m = 0; m < M; m += 1) {
      let sq = 0;
      for (let b = 0; b < B; b += 1) sq += gradEst[m * B + b] ** 2;
      if (sq > 0) {
        const rmsNow = Math.sqrt(sq / B);
        if (nextTouches[m] === 0) nextInitRms[m] = rmsNow;
        nextTouches[m] += 1;
        nextRms[m] = cfg.rmsBeta * prevRms[m] + (1 - cfg.rmsBeta) * (sq / B);
      }
    }

    const prevMom = prev?.mom ?? new Array(D).fill(0);
    const nextMom = new Array(D).fill(0);
    const schedule = cfg.baseEta / Math.sqrt(1 + cfg.stepDecay * stepIndex);
    let displacement = new Array(D).fill(0);

    for (let m = 0; m < M; m += 1) {
      const tc = Math.max(1, nextTouches[m]);
      const rmsHat = Math.sqrt(nextRms[m] / (1 - cfg.rmsBeta ** tc));
      const denom = Math.max(rmsHat, cfg.relFloor * nextInitRms[m]) + 1e-12;
      for (let b = 0; b < B; b += 1) {
        const idx = m * B + b;
        const scaledG = nextTouches[m] > 0 ? precondGrad[idx] / denom : 0;
        nextMom[idx] = cfg.momBeta * prevMom[idx] + (1 - cfg.momBeta) * scaledG;
        const momHat = nextMom[idx] / (1 - cfg.momBeta ** t || 1);
        displacement[idx] = -schedule * momHat;
      }
    }

    const cap = 0.5 * (1 + norm(theta));
    const dn = norm(displacement);
    if (dn > 1e-12) {
      if (dn > cap) budget.clamps += 1;
      const smoothScale = (cap * Math.tanh(dn / cap)) / dn;
      displacement = displacement.map(x => x * smoothScale);
    }

    nextTheta = theta.map((x, i) => x + displacement[i]);
    nextHistory = {
      objectiveId,
      dimension: D,
      t,
      blockRms: nextRms,
      initRms: nextInitRms,
      touches: nextTouches,
      mom: nextMom,
    };
  } else {
    // Conventional zero-order comparators: SPSA, Adam-SPSA, two-pair L-BFGS-SPSA
    const g = new Array(D).fill(0);
    for (let k = 0; k < 4; k += 1) {
      const d = Array.from({ length: D }, () => (rand() < 0.5 ? -1 : 1));
      const ptPlus = new Array(D);
      const ptMinus = new Array(D);
      for (let i = 0; i < D; i += 1) {
        ptPlus[i] = theta[i] + radius * d[i];
        ptMinus[i] = theta[i] - radius * d[i];
      }
      const slope = (window.query(ptPlus) - window.query(ptMinus)) / (8 * radius);
      for (let i = 0; i < D; i += 1) g[i] += slope * d[i];
    }

    const t = (prev?.t ?? 0) + 1;
    let displacement;
    nextHistory = { objectiveId, dimension: D, t, theta: [...theta], g: [...g] };

    if (method === 'spsa') {
      displacement = g.map(x => -rate * x);
    } else if (method === 'adam') {
      const mVec = g.map((x, i) => beta * (prev?.m?.[i] ?? 0) + (1 - beta) * x);
      const vVec = g.map((x, i) => 0.99 * (prev?.v?.[i] ?? 0) + 0.01 * x * x);
      nextHistory.m = mVec;
      nextHistory.v = vVec;
      displacement = g.map((_, i) => -rate * (mVec[i] / (1 - beta ** t)) / (Math.sqrt(vVec[i] / (1 - 0.99 ** t)) + 1e-8));
    } else if (method === 'bfgs') {
      const pairs = (prev?.pairs ?? []).map(p => ({ s: [...p.s], y: [...p.y], rho: p.rho }));
      if (prev?.theta && prev?.g) {
        const s = theta.map((x, i) => x - prev.theta[i]);
        const y = g.map((x, i) => x - prev.g[i]);
        const sy = dot(s, y);
        if (sy > 1e-10 * norm(s) * norm(y) && sy > 1e-12) {
          pairs.push({ s, y, rho: 1 / sy });
          if (pairs.length > 2) pairs.shift();
        } else {
          budget.skippedCurvature += 1;
        }
      }
      nextHistory.pairs = pairs;
      let q = [...g];
      const alpha = [];
      for (let i = pairs.length - 1; i >= 0; i -= 1) {
        alpha[i] = pairs[i].rho * dot(pairs[i].s, q);
        q = q.map((x, j) => x - alpha[i] * pairs[i].y[j]);
      }
      const last = pairs.at(-1);
      const scale = last ? clamp(dot(last.s, last.y) / dot(last.y, last.y), 0.001, 100) : 1;
      let rVec = q.map(x => scale * x);
      for (let i = 0; i < pairs.length; i += 1) {
        const b = pairs[i].rho * dot(pairs[i].y, rVec);
        rVec = rVec.map((x, j) => x + pairs[i].s[j] * (alpha[i] - b));
      }
      displacement = rVec.map(x => -rate * x);
    } else {
      throw new Error(`Unsupported conventional method: ${method}`);
    }

    const cap = 0.5 * (1 + norm(theta));
    const dn = norm(displacement);
    if (dn > cap) {
      budget.clamps += 1;
      displacement = displacement.map(x => (x * cap) / dn);
    }
    nextTheta = theta.map((x, i) => x + displacement[i]);
  }

  checkVector(nextTheta, D);
  const receipt = window.receipt();
  budget.scalarQueries += receipt.scalarQueries;
  budget.updates += 1;
  if (numericScalarCount(nextHistory) > 8 * D + 32) {
    throw new Error('Episode state scalar capacity exceeded');
  }
  budget.peakStateBytes = Math.max(budget.peakStateBytes, Buffer.byteLength(JSON.stringify(nextHistory)));
  return { theta: nextTheta, history: nextHistory };
}
