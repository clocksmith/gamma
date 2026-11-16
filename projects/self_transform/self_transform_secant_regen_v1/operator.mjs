import { createHash } from 'node:crypto';
import { Tape } from './autodiff.mjs';
import { gradientWindow } from './observation.mjs';

export const HIDDEN_UNITS = 5;
export const FEATURE_COUNT = 6;
export const PARAM_COUNT = 52;
export const SCHEMA = 'gamma.self-transform-secant-regen/v1';

export const CANDIDATE_RULES = [
  'secant_qn_trust',
  'diag_secant_trust',
  'secant_qn_no_rollback',
  'first_order_mlp_only',
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

export function checkVector(vec, expectedLength = vec?.length) {
  if (!Array.isArray(vec) || vec.length !== expectedLength || expectedLength < 1 || !vec.every(Number.isFinite)) {
    throw new Error(`Expected finite vector of length ${expectedLength}`);
  }
  return vec;
}

export function sha256(text) {
  return createHash('sha256').update(text).digest('hex');
}

function numericScalarCount(v) {
  if (typeof v === 'number') return 1;
  if (Array.isArray(v)) return v.reduce((s, x) => s + numericScalarCount(x), 0);
  if (v && typeof v === 'object') return Object.values(v).reduce((s, x) => s + numericScalarCount(x), 0);
  return 0;
}

// Exact IEEE-754 float64 little-endian artifact serialization for direct-serialization arms.
export function serialize(phi, rule = 'secant_qn_trust') {
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

// Exact recursive float64 state serialization for retained-state comparisons.
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

// Pure mathematical core of the self-applicable Secant-Trust Quasi-Newton Neural Transformer.
// Identical code updates task parameters (12D / 16D) and self-parameters Phi (52D).
export function applyNeuralRulePlain(theta, lossVal, grad, phi, rule, stepIndex, state) {
  if (!CANDIDATE_RULES.includes(rule)) throw new Error(`Unknown rule: ${rule}`);
  const D = theta.length;
  const sig = x => 0.5 * (1 + Math.tanh(0.5 * x));
  const clip3 = x => 3 * Math.tanh(x / 3);
  const absS = x => Math.sqrt(x * x + 1e-12);

  const initStep = 0.01 + 0.35 * sig(phi[45]);
  const secantScale = 0.15 + 1.60 * sig(phi[46]);
  const qnMix = (rule === 'diag_secant_trust' || rule === 'first_order_mlp_only') ? 0 : sig(phi[47]);
  const diagMix = rule === 'first_order_mlp_only' ? 0 : sig(phi[48]);
  const backtrack = rule === 'secant_qn_no_rollback' ? 0 : 0.92 * sig(phi[49]);
  const capScale = 0.08 + 0.90 * sig(phi[50]);
  const nesterov = 0.75 * sig(phi[51]);

  const initLoss = state ? state.initLoss : lossVal;
  let anchorTheta = theta;
  let anchorGrad = grad;
  let bestLoss = lossVal;
  let bestTheta = [...theta];
  let bestGrad = [...grad];
  let lossSignal = 0;

  if (state !== null) {
    // Strictly affine-invariant loss scale: depends only on loss differences (initLoss - bestLoss, lossVal - bestLoss)!
    const scaleL = absS(initLoss - state.bestLoss) + absS(lossVal - state.prevLoss) + 1e-8;
    const diffL = lossVal - state.bestLoss;
    lossSignal = clip3(diffL / scaleL);
    const worseGate = sig(10.0 * (diffL / scaleL));
    const pull = backtrack * worseGate;
    anchorTheta = theta.map((x, i) => (1 - pull) * x + pull * state.bestTheta[i]);
    anchorGrad = grad.map((g, i) => (1 - pull) * g + pull * state.bestGrad[i]);
    const keep = 1 - worseGate;
    bestLoss = keep * lossVal + worseGate * state.bestLoss;
    bestTheta = theta.map((x, i) => keep * x + worseGate * state.bestTheta[i]);
    bestGrad = grad.map((g, i) => keep * g + worseGate * state.bestGrad[i]);
  }

  let gSq = 1e-12;
  let thSq0 = 1e-12;
  for (let i = 0; i < D; i += 1) {
    gSq += anchorGrad[i] ** 2;
    thSq0 += anchorTheta[i] ** 2;
  }
  const gRms = Math.sqrt(gSq / D) + 1e-12;
  const thScale = 0.15 + Math.sqrt(thSq0 / D);

  let qnDir = anchorGrad.map(g => g / gRms);
  let stepLen = initStep * thScale;

  if (state !== null && rule !== 'first_order_mlp_only') {
    const s = theta.map((x, i) => x - state.prevTheta[i]);
    const y = grad.map((g, i) => g - state.prevGrad[i]);
    let sy = 0;
    let sNormSq = 1e-12;
    let yNormSq = 1e-12;
    for (let i = 0; i < D; i += 1) {
      sy += s[i] * y[i];
      sNormSq += s[i] ** 2;
      yNormSq += y[i] ** 2;
    }
    const rawBbStep = Math.sqrt(sNormSq / yNormSq) * gRms;
    const maxBb = 1.5 * thScale;
    stepLen = secantScale * (maxBb * Math.tanh(rawBbStep / maxBb));

    const snyn = Math.sqrt(sNormSq * yNormSq) + 1e-12;
    const posCurvGate = sig((5.0 * sy) / snyn);
    const denomSy = absS(sy) + 0.1 * Math.sqrt(sNormSq * yNormSq) + 1e-12;
    let sg = 0;
    for (let i = 0; i < D; i += 1) sg += s[i] * anchorGrad[i];
    const alpha = sg / denomSy;
    // Scale-invariant secant scaling: (s^T y) / ||y||^2 * (||y|| / ||s||) = cos(s, y) in [-1, 1]!
    // Wait: in H*g, s*alpha has units [s]*([s]*[g]/([s]*[y])) = [s]*[g]/[y], while gamma*q must ALSO have units [s]*[g]/[y]!
    // So gamma = (s^T y) / ||y||^2 has exact units [s]/[y], making hgRank1 homogeneous of degree 0 in objective scale!
    const invCurvScale = Math.sqrt(sNormSq / yNormSq);
    const cosSy = sy / snyn;
    const gamma = invCurvScale * (0.15 + 1.70 * sig(3.0 * cosSy));
    const q = anchorGrad.map((g, i) => g - alpha * y[i]);
    let yq = 0;
    for (let i = 0; i < D; i += 1) yq += y[i] * q[i];
    const beta = (gamma * yq) / denomSy;
    const hgRank1 = q.map((qi, i) => gamma * qi + s[i] * (alpha - beta));
    let hgSq = 1e-12;
    for (let i = 0; i < D; i += 1) hgSq += hgRank1[i] ** 2;
    const hgRms = Math.sqrt(hgSq / D) + 1e-12;

    const sRef = 0.1 * Math.sqrt(sNormSq / D);
    const yRef = 0.1 * Math.sqrt(yNormSq / D) + 1e-12;
    const diagDir = anchorGrad.map((g, i) => {
      // Normalized coordinate inverse-curvature relative to RMS inverse-curvature -> strictly scale invariant!
      const relRatio = ((absS(s[i]) + sRef) / (absS(y[i]) + yRef)) / (invCurvScale + 1e-12);
      return g * (2.5 * Math.tanh(relRatio / 2.5));
    });
    let dgSq = 1e-12;
    for (let i = 0; i < D; i += 1) dgSq += diagDir[i] ** 2;
    const dgRms = Math.sqrt(dgSq / D) + 1e-12;

    qnDir = anchorGrad.map((g, i) => {
      const baseD = g / gRms;
      const r1D = posCurvGate * (hgRank1[i] / hgRms) + (1 - posCurvGate) * baseD;
      const dD = diagDir[i] / dgRms;
      const firstPart = (1 - diagMix) * baseD + diagMix * dD;
      return (1 - qnMix) * firstPart + qnMix * r1D;
    });
  }

  const prevMom = state?.mom ?? new Array(D).fill(0);
  const prevG = state?.prevGrad ?? anchorGrad;
  const prevGain = state?.gain ?? new Array(D).fill(0);
  const progress = Math.tanh(stepIndex * 0.15);

  const nextMom = new Array(D);
  const nextGain = new Array(D);
  const rawDisp = new Array(D);

  for (let i = 0; i < D; i += 1) {
    const gn = clip3(anchorGrad[i] / gRms);
    const pn = clip3(prevG[i] / gRms);
    const qn = clip3(qnDir[i]);
    const agree = Math.tanh(2.0 * gn * pn);
    const mPrev = prevMom[i];
    const feats = [gn, qn, mPrev, agree, lossSignal, progress];

    const h = new Array(HIDDEN_UNITS);
    for (let k = 0; k < HIDDEN_UNITS; k += 1) {
      let sum = phi[30 + k];
      const row = k * FEATURE_COUNT;
      for (let j = 0; j < FEATURE_COUNT; j += 1) sum += phi[row + j] * feats[j];
      h[k] = Math.tanh(sum);
    }
    let gOut = 0;
    let mOut = 0;
    for (let k = 0; k < HIDDEN_UNITS; k += 1) {
      gOut += phi[35 + k] * h[k];
      mOut += phi[40 + k] * h[k];
    }
    const mBlend = 0.85 * sig(mOut);
    const mNew = mBlend * mPrev + (1 - mBlend) * qn;
    const look = (1 - nesterov) * mNew + nesterov * (mBlend * mNew + (1 - mBlend) * qn);
    const gNew = 1.4 * Math.tanh(0.75 * prevGain[i] + 0.55 * Math.tanh(gOut));
    rawDisp[i] = -stepLen * Math.exp(gNew) * look;
    nextMom[i] = mNew;
    nextGain[i] = gNew;
  }

  let nTh = 1e-12;
  let nD = 1e-12;
  for (let i = 0; i < D; i += 1) {
    nTh += anchorTheta[i] ** 2;
    nD += rawDisp[i] ** 2;
  }
  const cap = capScale * (1 + Math.sqrt(nTh));
  const dn = Math.sqrt(nD);
  const clamped = dn > cap;
  const sc = (cap * Math.tanh(dn / cap)) / dn;
  const nextTheta = anchorTheta.map((x, i) => x + sc * rawDisp[i]);

  return {
    theta: nextTheta,
    clamped,
    state: {
      initLoss,
      prevLoss: lossVal,
      prevTheta: [...theta],
      prevGrad: [...grad],
      bestLoss,
      bestTheta,
      bestGrad,
      mom: nextMom,
      gain: nextGain,
    },
  };
}

// Exact reverse-mode Tape twin of applyNeuralRulePlain (machine-epsilon identical forward path).
export function applyNeuralRuleTape(tape, thetaIds, lossId, gradIds, phiIds, rule, stepIndex, stateIds) {
  const D = thetaIds.length;
  const sig = id => tape.scale(tape.addConst(tape.tanh(tape.scale(id, 0.5)), 1), 0.5);
  const clip3 = id => tape.scale(tape.tanh(tape.scale(id, 1 / 3)), 3);
  const absS = id => tape.sqrt(tape.addConst(tape.mul(id, id), 1e-12));
  const zId = tape.const(0);

  const initStep = tape.addConst(tape.scale(sig(phiIds[45]), 0.35), 0.01);
  const secantScale = tape.addConst(tape.scale(sig(phiIds[46]), 1.60), 0.15);
  const qnMix = (rule === 'diag_secant_trust' || rule === 'first_order_mlp_only') ? zId : sig(phiIds[47]);
  const diagMix = rule === 'first_order_mlp_only' ? zId : sig(phiIds[48]);
  const backtrack = rule === 'secant_qn_no_rollback' ? zId : tape.scale(sig(phiIds[49]), 0.92);
  const capScale = tape.addConst(tape.scale(sig(phiIds[50]), 0.90), 0.08);
  const nesterov = tape.scale(sig(phiIds[51]), 0.75);

  const initLoss = stateIds ? stateIds.initLoss : lossId;
  let anchorTheta = thetaIds;
  let anchorGrad = gradIds;
  let bestLoss = lossId;
  let bestTheta = [...thetaIds];
  let bestGrad = [...gradIds];
  let lossSignal = zId;

  if (stateIds !== null) {
    const scaleL = tape.addConst(
      tape.add(absS(tape.sub(initLoss, stateIds.bestLoss)), absS(tape.sub(lossId, stateIds.prevLoss))),
      1e-8,
    );
    const diffL = tape.sub(lossId, stateIds.bestLoss);
    lossSignal = clip3(tape.div(diffL, scaleL));
    const worseGate = sig(tape.scale(tape.div(diffL, scaleL), 10.0));
    const pull = tape.mul(backtrack, worseGate);
    const omp = tape.addConst(tape.scale(pull, -1), 1);
    anchorTheta = thetaIds.map((x, i) => tape.add(tape.mul(omp, x), tape.mul(pull, stateIds.bestTheta[i])));
    anchorGrad = gradIds.map((g, i) => tape.add(tape.mul(omp, g), tape.mul(pull, stateIds.bestGrad[i])));
    const keep = tape.addConst(tape.scale(worseGate, -1), 1);
    bestLoss = tape.add(tape.mul(keep, lossId), tape.mul(worseGate, stateIds.bestLoss));
    bestTheta = thetaIds.map((x, i) => tape.add(tape.mul(keep, x), tape.mul(worseGate, stateIds.bestTheta[i])));
    bestGrad = gradIds.map((g, i) => tape.add(tape.mul(keep, g), tape.mul(worseGate, stateIds.bestGrad[i])));
  }

  let gSq = tape.const(1e-12);
  let thSq0 = tape.const(1e-12);
  for (let i = 0; i < D; i += 1) {
    gSq = tape.add(gSq, tape.mul(anchorGrad[i], anchorGrad[i]));
    thSq0 = tape.add(thSq0, tape.mul(anchorTheta[i], anchorTheta[i]));
  }
  const gRms = tape.addConst(tape.sqrt(tape.scale(gSq, 1 / D)), 1e-12);
  const thScale = tape.addConst(tape.sqrt(tape.scale(thSq0, 1 / D)), 0.15);

  let qnDir = anchorGrad.map(g => tape.div(g, gRms));
  let stepLen = tape.mul(initStep, thScale);

  if (stateIds !== null && rule !== 'first_order_mlp_only') {
    const s = thetaIds.map((x, i) => tape.sub(x, stateIds.prevTheta[i]));
    const y = gradIds.map((g, i) => tape.sub(g, stateIds.prevGrad[i]));
    let sy = zId;
    let sNormSq = tape.const(1e-12);
    let yNormSq = tape.const(1e-12);
    for (let i = 0; i < D; i += 1) {
      sy = tape.add(sy, tape.mul(s[i], y[i]));
      sNormSq = tape.add(sNormSq, tape.mul(s[i], s[i]));
      yNormSq = tape.add(yNormSq, tape.mul(y[i], y[i]));
    }
    const invCurvScale = tape.sqrt(tape.div(sNormSq, yNormSq));
    const rawBbStep = tape.mul(invCurvScale, gRms);
    const maxBb = tape.scale(thScale, 1.5);
    stepLen = tape.mul(secantScale, tape.mul(maxBb, tape.tanh(tape.div(rawBbStep, maxBb))));

    const snyn = tape.addConst(tape.sqrt(tape.mul(sNormSq, yNormSq)), 1e-12);
    const posCurvGate = sig(tape.scale(tape.div(sy, snyn), 5.0));
    const denomSy = tape.addConst(tape.add(absS(sy), tape.scale(tape.sqrt(tape.mul(sNormSq, yNormSq)), 0.1)), 1e-12);
    let sg = zId;
    for (let i = 0; i < D; i += 1) sg = tape.add(sg, tape.mul(s[i], anchorGrad[i]));
    const alpha = tape.div(sg, denomSy);
    const cosSy = tape.div(sy, snyn);
    const gamma = tape.mul(invCurvScale, tape.addConst(tape.scale(sig(tape.scale(cosSy, 3.0)), 1.70), 0.15));
    const q = anchorGrad.map((g, i) => tape.sub(g, tape.mul(alpha, y[i])));
    let yq = zId;
    for (let i = 0; i < D; i += 1) yq = tape.add(yq, tape.mul(y[i], q[i]));
    const beta = tape.div(tape.mul(gamma, yq), denomSy);
    const aMinusB = tape.sub(alpha, beta);
    const hgRank1 = q.map((qi, i) => tape.add(tape.mul(gamma, qi), tape.mul(s[i], aMinusB)));
    let hgSq = tape.const(1e-12);
    for (let i = 0; i < D; i += 1) hgSq = tape.add(hgSq, tape.mul(hgRank1[i], hgRank1[i]));
    const hgRms = tape.addConst(tape.sqrt(tape.scale(hgSq, 1 / D)), 1e-12);

    const sRef = tape.scale(tape.sqrt(tape.scale(sNormSq, 1 / D)), 0.1);
    const yRef = tape.addConst(tape.scale(tape.sqrt(tape.scale(yNormSq, 1 / D)), 0.1), 1e-12);
    const invRef = tape.addConst(invCurvScale, 1e-12);
    const diagDir = anchorGrad.map((g, i) => {
      const relRatio = tape.div(tape.div(tape.add(absS(s[i]), sRef), tape.add(absS(y[i]), yRef)), invRef);
      return tape.mul(g, tape.scale(tape.tanh(tape.scale(relRatio, 1 / 2.5)), 2.5));
    });
    let dgSq = tape.const(1e-12);
    for (let i = 0; i < D; i += 1) dgSq = tape.add(dgSq, tape.mul(diagDir[i], diagDir[i]));
    const dgRms = tape.addConst(tape.sqrt(tape.scale(dgSq, 1 / D)), 1e-12);

    const omQn = tape.addConst(tape.scale(qnMix, -1), 1);
    const omDg = tape.addConst(tape.scale(diagMix, -1), 1);
    const omPc = tape.addConst(tape.scale(posCurvGate, -1), 1);
    qnDir = anchorGrad.map((g, i) => {
      const baseD = tape.div(g, gRms);
      const r1D = tape.add(tape.mul(posCurvGate, tape.div(hgRank1[i], hgRms)), tape.mul(omPc, baseD));
      const dD = tape.div(diagDir[i], dgRms);
      const firstPart = tape.add(tape.mul(omDg, baseD), tape.mul(diagMix, dD));
      return tape.add(tape.mul(omQn, firstPart), tape.mul(qnMix, r1D));
    });
  }

  const prevMom = stateIds?.mom ?? new Array(D).fill(zId);
  const prevG = stateIds?.prevGrad ?? anchorGrad;
  const prevGain = stateIds?.gain ?? new Array(D).fill(zId);
  const progress = tape.const(Math.tanh(stepIndex * 0.15));
  const omNest = tape.addConst(tape.scale(nesterov, -1), 1);

  const nextMom = new Array(D);
  const nextGain = new Array(D);
  const rawDisp = new Array(D);

  for (let i = 0; i < D; i += 1) {
    const gn = clip3(tape.div(anchorGrad[i], gRms));
    const pn = clip3(tape.div(prevG[i], gRms));
    const qn = clip3(qnDir[i]);
    const agree = tape.tanh(tape.scale(tape.mul(gn, pn), 2.0));
    const mPrev = prevMom[i];
    const feats = [gn, qn, mPrev, agree, lossSignal, progress];

    const h = new Array(HIDDEN_UNITS);
    for (let k = 0; k < HIDDEN_UNITS; k += 1) {
      let sum = phiIds[30 + k];
      const row = k * FEATURE_COUNT;
      for (let j = 0; j < FEATURE_COUNT; j += 1) sum = tape.add(sum, tape.mul(phiIds[row + j], feats[j]));
      h[k] = tape.tanh(sum);
    }
    let gOut = zId;
    let mOut = zId;
    for (let k = 0; k < HIDDEN_UNITS; k += 1) {
      gOut = tape.add(gOut, tape.mul(phiIds[35 + k], h[k]));
      mOut = tape.add(mOut, tape.mul(phiIds[40 + k], h[k]));
    }
    const mBlend = tape.scale(sig(mOut), 0.85);
    const omB = tape.addConst(tape.scale(mBlend, -1), 1);
    const mNew = tape.add(tape.mul(mBlend, mPrev), tape.mul(omB, qn));
    const look = tape.add(tape.mul(omNest, mNew), tape.mul(nesterov, tape.add(tape.mul(mBlend, mNew), tape.mul(omB, qn))));
    const gNew = tape.scale(tape.tanh(tape.add(tape.scale(prevGain[i], 0.75), tape.scale(tape.tanh(gOut), 0.55))), 1.4);
    rawDisp[i] = tape.scale(tape.mul(stepLen, tape.mul(tape.exp(gNew), look)), -1);
    nextMom[i] = mNew;
    nextGain[i] = gNew;
  }

  let nTh = tape.const(1e-12);
  let nD = tape.const(1e-12);
  for (let i = 0; i < D; i += 1) {
    nTh = tape.add(nTh, tape.mul(anchorTheta[i], anchorTheta[i]));
    nD = tape.add(nD, tape.mul(rawDisp[i], rawDisp[i]));
  }
  const cap = tape.mul(capScale, tape.addConst(tape.sqrt(nTh), 1));
  const dn = tape.sqrt(nD);
  const sc = tape.div(tape.mul(cap, tape.tanh(tape.div(dn, cap))), dn);
  const nextTheta = anchorTheta.map((x, i) => tape.add(x, tape.mul(sc, rawDisp[i])));

  return {
    thetaIds: nextTheta,
    stateIds: {
      initLoss,
      prevLoss: lossId,
      prevTheta: [...thetaIds],
      prevGrad: [...gradIds],
      bestLoss,
      bestTheta,
      bestGrad,
      mom: nextMom,
      gain: nextGain,
    },
  };
}

// Universal single-step update gated by gradientWindow(limit = 1).
export function step({
  theta,
  phi = null,
  rule = 'secant_qn_trust',
  method = 'learned',
  rate = 0.05,
  beta = 0.9,
  objectiveId,
  lossAndGrad,
  stepIndex = 0,
  history = null,
}, budget) {
  checkVector(theta);
  const D = theta.length;
  const win = gradientWindow({ objectiveId, theta, previous: history, lossAndGrad, limit: 1 });
  let obs;
  try {
    obs = win.evaluate(theta);
  } catch (err) {
    const rec = win.receipt();
    budget.oracleCalls += rec.oracleCalls;
    budget.failedAttempts += rec.failedAttempts;
    throw err;
  }
  const prev = win.history;
  let nextTheta;
  let nextHistory;

  if (method === 'learned') {
    checkVector(phi, PARAM_COUNT);
    const innerState = prev?.inner ?? null;
    const out = applyNeuralRulePlain(theta, obs.loss, obs.grad, phi, rule, stepIndex, innerState);
    if (out.clamped) budget.clamps += 1;
    nextTheta = out.theta;
    nextHistory = { objectiveId, dimension: D, t: (prev?.t ?? 0) + 1, inner: out.state };
  } else {
    const t = (prev?.t ?? 0) + 1;
    const grad = obs.grad;
    nextHistory = { objectiveId, dimension: D, t, theta: [...theta], g: [...grad] };
    let disp;

    if (method === 'sgd') {
      const m = grad.map((g, i) => beta * (prev?.m?.[i] ?? 0) + g);
      nextHistory.m = m;
      disp = m.map(x => -rate * x);
    } else if (method === 'adam') {
      const m = grad.map((g, i) => beta * (prev?.m?.[i] ?? 0) + (1 - beta) * g);
      const v = grad.map((g, i) => 0.99 * (prev?.v?.[i] ?? 0) + 0.01 * g * g);
      nextHistory.m = m;
      nextHistory.v = v;
      disp = grad.map((_, i) => -rate * (m[i] / (1 - beta ** t)) / (Math.sqrt(v[i] / (1 - 0.99 ** t)) + 1e-8));
    } else if (method === 'bfgs') {
      const pairs = (prev?.pairs ?? []).map(p => ({ s: [...p.s], y: [...p.y], rho: p.rho }));
      if (prev?.theta && prev?.g) {
        const s = theta.map((x, i) => x - prev.theta[i]);
        const y = grad.map((g, i) => g - prev.g[i]);
        let sy = 0;
        let ns = 0;
        let ny = 0;
        for (let i = 0; i < D; i += 1) {
          sy += s[i] * y[i];
          ns += s[i] ** 2;
          ny += y[i] ** 2;
        }
        if (sy > 1e-10 * Math.sqrt(ns * ny) && sy > 1e-12) {
          pairs.push({ s, y, rho: 1 / sy });
          if (pairs.length > 3) pairs.shift();
        } else {
          budget.skippedCurvature += 1;
        }
      }
      nextHistory.pairs = pairs;
      let q = [...grad];
      const al = [];
      for (let i = pairs.length - 1; i >= 0; i -= 1) {
        let sq = 0;
        for (let j = 0; j < D; j += 1) sq += pairs[i].s[j] * q[j];
        al[i] = pairs[i].rho * sq;
        q = q.map((x, j) => x - al[i] * pairs[i].y[j]);
      }
      const last = pairs.at(-1);
      let sc = 1;
      if (last) {
        let sy = 0;
        let yy = 0;
        for (let j = 0; j < D; j += 1) {
          sy += last.s[j] * last.y[j];
          yy += last.y[j] ** 2;
        }
        sc = Math.max(0.001, Math.min(100, sy / yy));
      }
      let rVec = q.map(x => sc * x);
      for (let i = 0; i < pairs.length; i += 1) {
        let yr = 0;
        for (let j = 0; j < D; j += 1) yr += pairs[i].y[j] * rVec[j];
        const b = pairs[i].rho * yr;
        rVec = rVec.map((x, j) => x + pairs[i].s[j] * (al[i] - b));
      }
      disp = rVec.map(x => -rate * x);
    } else {
      throw new Error(`Unsupported conventional method: ${method}`);
    }

    let nTh = 1e-12;
    let nD = 1e-12;
    for (let i = 0; i < D; i += 1) {
      nTh += theta[i] ** 2;
      nD += disp[i] ** 2;
    }
    const cap = 0.90 * (1 + Math.sqrt(nTh));
    const dn = Math.sqrt(nD);
    if (dn > cap) {
      budget.clamps += 1;
      disp = disp.map(x => (x * cap) / dn);
    }
    nextTheta = theta.map((x, i) => x + disp[i]);
  }

  checkVector(nextTheta, D);
  const rec = win.receipt();
  budget.oracleCalls += rec.oracleCalls;
  budget.failedAttempts += rec.failedAttempts;
  budget.updates += 1;
  if (numericScalarCount(nextHistory) > 12 * D + 32) {
    throw new Error('Episode state scalar capacity exceeded');
  }
  budget.peakStateBytes = Math.max(budget.peakStateBytes, Buffer.byteLength(JSON.stringify(nextHistory)));
  return { theta: nextTheta, history: nextHistory };
}

// ============================================================================
// Weight-Free Behavioral-Transcript Neural Regeneration
// ============================================================================
// Parent emits ONLY input-output behavioral responses on deterministic synthetic probe states.
// Zero raw parameter values or weightsHex ever cross the regeneration channel.
// In the cold subprocess, a blank all-zero network Phi_0 = zeros(52) bootstraps itself using
// its own currently-regenerating neural update rule (st.theta) to match the behavioral transcript!

export function emitBehavioralTranscript(phi, rule = 'secant_qn_trust', probeCount = 24, probeSeed = 424242) {
  checkVector(phi, PARAM_COUNT);
  const r = rng(probeSeed);
  const probes = [];
  for (let k = 0; k < probeCount; k += 1) {
    const D = 6;
    const th = Array.from({ length: D }, () => normal(r) * 0.6);
    const g = Array.from({ length: D }, () => normal(r) * 1.2);
    const L = 0.5 + r() * 3.0;
    const hasState = k % 2 === 1;
    const prevTh = th.map(x => x - normal(r) * 0.15);
    const prevG = g.map(x => x - normal(r) * 0.8);
    const st = hasState ? {
      initLoss: L + 0.6,
      prevLoss: L + 0.25,
      prevTheta: prevTh,
      prevGrad: prevG,
      bestLoss: L + (k % 4 === 3 ? -0.35 : 0.15),
      bestTheta: prevTh,
      bestGrad: prevG,
      mom: Array.from({ length: D }, () => normal(r) * 0.4),
      gain: Array.from({ length: D }, () => normal(r) * 0.3),
    } : null;
    const stepIdx = k % 8;
    const out = applyNeuralRulePlain(th, L, g, phi, rule, stepIdx, st);
    probes.push({ th, L, g, st, stepIdx, targetNextTheta: out.theta });
  }
  const payload = { schema: `${SCHEMA}-transcript`, rule, probeCount, probeSeed, probes };
  return JSON.stringify({ ...payload, sha256: sha256(JSON.stringify(payload)) });
}

export function parseBehavioralTranscript(text) {
  const parsed = JSON.parse(text);
  // Explicitly reject any payload smuggling raw weight keys!
  if ('weightsHex' in parsed || 'phi' in parsed || 'weights' in parsed) {
    throw new Error('Weight-smuggling rejected in behavioral regeneration channel');
  }
  const keys = Object.keys(parsed).sort().join(',');
  if (keys !== 'probeCount,probeSeed,probes,rule,schema,sha256'
      || parsed.schema !== `${SCHEMA}-transcript`
      || !CANDIDATE_RULES.includes(parsed.rule)) {
    throw new Error('Invalid behavioral regeneration transcript');
  }
  const payload = {
    schema: parsed.schema,
    rule: parsed.rule,
    probeCount: parsed.probeCount,
    probeSeed: parsed.probeSeed,
    probes: parsed.probes,
  };
  if (sha256(JSON.stringify(payload)) !== parsed.sha256) {
    throw new Error('Behavioral transcript SHA-256 mismatch');
  }
  return payload;
}

export function regenerateFromTranscript(transcriptText, regenSteps = 16, budget) {
  const { rule, probes } = parseBehavioralTranscript(transcriptText);
  budget.reconstructionBytes += Buffer.byteLength(transcriptText);

  const rBlank = rng(1337);
  const blankPhi = Array.from({ length: PARAM_COUNT }, () => normal(rBlank) * 0.12);
  const behavioralLossAndGrad = candPhi => {
    const tape = new Tape();
    const pIds = candPhi.map(x => tape.var(x));
    let total = tape.const(0);
    const invK = 1 / probes.length;
    for (const pr of probes) {
      const D = pr.th.length;
      const thIds = pr.th.map(x => tape.const(x));
      const lossId = tape.const(pr.L);
      const gradIds = pr.g.map(x => tape.const(x));
      const stIds = pr.st ? {
        initLoss: tape.const(pr.st.initLoss),
        prevLoss: tape.const(pr.st.prevLoss),
        prevTheta: pr.st.prevTheta.map(x => tape.const(x)),
        prevGrad: pr.st.prevGrad.map(x => tape.const(x)),
        bestLoss: tape.const(pr.st.bestLoss),
        bestTheta: pr.st.bestTheta.map(x => tape.const(x)),
        bestGrad: pr.st.bestGrad.map(x => tape.const(x)),
        mom: pr.st.mom.map(x => tape.const(x)),
        gain: pr.st.gain.map(x => tape.const(x)),
      } : null;
      const out = applyNeuralRuleTape(tape, thIds, lossId, gradIds, pIds, rule, pr.stepIdx, stIds);
      for (let i = 0; i < D; i += 1) {
        const diff = tape.addConst(out.thetaIds[i], -pr.targetNextTheta[i]);
        total = tape.add(total, tape.scale(tape.mul(diff, diff), invK / D));
      }
    }
    tape.backward(total);
    budget.regenerationFlops += tape.nodes.length * 4;
    return {
      loss: tape.nodes[total].val,
      grad: pIds.map(id => tape.nodes[id].grad),
    };
  };

  const initialMse = behavioralLossAndGrad(blankPhi).loss;
  budget.regenerationCalls += 1;

  let state = { theta: [...blankPhi], history: null };
  for (let s = 0; s < regenSteps; s += 1) {
    // True self-bootstrapping: newborn uses its OWN current weights state.theta to regenerate itself!
    const stepBudget = {
      oracleCalls: 0, failedAttempts: 0, updates: 0, clamps: 0, skippedCurvature: 0,
      regenerationCalls: 0, regenerationFlops: 0, reconstructionBytes: 0, peakStateBytes: 0,
    };
    state = step({
      theta: state.theta,
      phi: state.theta,
      rule,
      method: 'learned',
      objectiveId: 'regen-distill',
      lossAndGrad: behavioralLossAndGrad,
      stepIndex: s,
      history: state.history,
    }, stepBudget);
    budget.regenerationCalls += stepBudget.oracleCalls;
    budget.failedAttempts += stepBudget.failedAttempts;
    budget.updates += stepBudget.updates;
    budget.clamps += stepBudget.clamps;
    budget.peakStateBytes = Math.max(budget.peakStateBytes, stepBudget.peakStateBytes);
  }

  const finalMse = behavioralLossAndGrad(state.theta).loss;
  budget.regenerationCalls += 1;

  return {
    phi: state.theta,
    rule,
    initialBehavioralMse: initialMse,
    finalBehavioralMse: finalMse,
  };
}
