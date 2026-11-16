import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { Tape } from './autodiff.mjs';
import { counter, gradientWindow } from './observation.mjs';
import {
  CANDIDATE_RULES,
  PARAM_COUNT,
  applyNeuralRulePlain,
  applyNeuralRuleTape,
  emitBehavioralTranscript,
  freezeState,
  parseBehavioralTranscript,
  reconstruct,
  regenerateFromTranscript,
  restoreState,
  serialize,
  step,
} from './operator.mjs';
import {
  FAMILIES,
  evaluateRule,
  initializeAndCalibrate,
  mean,
  metaLossAndGrad,
  proposeSuccessor,
  sampleTasks,
} from './tasks.mjs';
import { signProbability, summarizeEffects } from './stats.mjs';

// 1. Oracle budget cap, deep-copy isolation, and failed-attempt charging
{
  const prev = { objectiveId: 'obj-1', dimension: 3, t: 1, vec: [1, 2, 3] };
  const win = gradientWindow({
    objectiveId: 'obj-1',
    theta: [0, 0, 0],
    previous: prev,
    lossAndGrad: pt => ({ loss: pt[0] ** 2, grad: [2 * pt[0], 0, 0] }),
    limit: 2,
  });
  prev.vec[0] = 999;
  assert.equal(win.history.vec[0], 1, 'State must be deep-cloned');
  assert.deepEqual(win.evaluate([2, 0, 0]), { loss: 4, grad: [4, 0, 0] });
  assert.equal(win.receipt().oracleCalls, 1);

  const badWin = gradientWindow({
    objectiveId: 'bad',
    theta: [0, 0],
    lossAndGrad: () => ({ loss: NaN, grad: [0, 0] }),
    limit: 2,
  });
  assert.throws(() => badWin.evaluate([0, 0]), /Non-finite/);
  assert.equal(badWin.receipt().oracleCalls, 1);
  assert.equal(badWin.receipt().failedAttempts, 1, 'Failed observation must charge failedAttempts and oracleCalls');

  const bFail = counter();
  assert.throws(() => step({
    theta: [1, 2],
    method: 'sgd',
    objectiveId: 'boom',
    lossAndGrad: () => { throw new Error('oracle crash'); },
  }, bFail), /oracle crash/);
  assert.equal(bFail.oracleCalls, 1);
  assert.equal(bFail.failedAttempts, 1);
}
console.log('[pass] gradientWindow budget cap, isolation, and failed-attempt charging');

// 2. Exact reverse-mode autodiff Tape parity against analytical plain execution across all 4 rules & 2 task families
{
  const phi = Array.from({ length: PARAM_COUNT }, (_, i) => Math.sin(i + 1) * 0.18);
  for (const family of FAMILIES) {
    const tasks = sampleTasks(family, 42, 3);
    for (const rule of CANDIDATE_RULES) {
      const plainLoss = mean(evaluateRule(phi, rule, tasks, 5, counter()));
      const tapeRes = metaLossAndGrad(phi, rule, tasks, 5, counter());
      assert.ok(Math.abs(plainLoss - tapeRes.loss) < 1e-12, `Tape/plain loss drift on ${family}/${rule}`);
      // Finite-difference spot check on meta-gradient wrt phi[0] and phi[46]
      const eps = 1e-6;
      for (const idx of [0, 31, 46, 49]) {
        const pPlus = [...phi]; pPlus[idx] += eps;
        const pMinus = [...phi]; pMinus[idx] -= eps;
        const fd = (mean(evaluateRule(pPlus, rule, tasks, 5, counter()))
          - mean(evaluateRule(pMinus, rule, tasks, 5, counter()))) / (2 * eps);
        assert.ok(Math.abs(fd - tapeRes.grad[idx]) < 1e-5, `Meta-grad FD mismatch at ${idx} (${rule}): ${fd} vs ${tapeRes.grad[idx]}`);
      }
    }
  }
}
console.log('[pass] exact reverse-mode autodiff forward & meta-gradient finite-difference checks');

// 3. Affine objective invariance L(theta) -> 1000 * L(theta) + 500 across multi-step trajectories
{
  const phi = Array.from({ length: PARAM_COUNT }, (_, i) => Math.cos(i * 0.5) * 0.2);
  const baseTask = sampleTasks('twisted_huber_valley', 99, 1)[0];
  for (const rule of CANDIDATE_RULES) {
    let stBase = { theta: [...baseTask.initial], history: null };
    let stAff = { theta: [...baseTask.initial], history: null };
    for (let s = 0; s < 5; s += 1) {
      stBase = step({
        theta: stBase.theta,
        phi,
        rule,
        method: 'learned',
        objectiveId: 'aff-1',
        lossAndGrad: w => baseTask.lossAndGradPlain(w),
        stepIndex: s,
        history: stBase.history,
      }, counter());
      stAff = step({
        theta: stAff.theta,
        phi,
        rule,
        method: 'learned',
        objectiveId: 'aff-1',
        lossAndGrad: w => {
          const r = baseTask.lossAndGradPlain(w);
          return { loss: 1000 * r.loss + 500, grad: r.grad.map(g => 1000 * g) };
        },
        stepIndex: s,
        history: stAff.history,
      }, counter());
    }
    for (let i = 0; i < stBase.theta.length; i += 1) {
      assert.ok(Math.abs(stBase.theta[i] - stAff.theta[i]) < 1e-7, `Affine invariance drift on ${rule} at ${i}`);
    }
  }
}
console.log('[pass] multi-step affine objective invariance (L -> 1000*L + 500)');

// 4. Artifact serialization (-0 fidelity + corruption rejection) & weight-free behavioral neural regeneration
{
  const phi = Array.from({ length: PARAM_COUNT }, (_, i) => (i === 0 ? -0 : Math.sin(i) * 0.25));
  const art = serialize(phi, 'secant_qn_trust');
  const rec = reconstruct(art);
  assert.ok(Object.is(rec.phi[0], -0));
  assert.equal(serialize(rec.phi, rec.rule), art);
  const bad = JSON.parse(art);
  bad.weightsHex = `ff${bad.weightsHex.slice(2)}`;
  assert.throws(() => reconstruct(JSON.stringify(bad)), /SHA-256/);

  const st = { objectiveId: 'x', dimension: 4, arr: [-0, 1.25] };
  const rSt = restoreState(freezeState(st));
  assert.ok(Object.is(rSt.arr[0], -0));

  // Behavioral transcript rejects smuggled weights and regenerates functional behavior from blank zeros(52)
  const tr = emitBehavioralTranscript(phi, 'secant_qn_trust', 24, 424242);
  assert.ok(!tr.includes('weightsHex'));
  assert.throws(() => parseBehavioralTranscript(JSON.stringify({ ...JSON.parse(tr), weightsHex: '00' })), /Weight-smuggling/);
  const rBudget = counter();
  const regen = regenerateFromTranscript(tr, 16, rBudget);
  assert.ok(regen.finalBehavioralMse < 0.05 * regen.initialBehavioralMse, 'Self-bootstrapped neural regeneration must reduce behavioral MSE by >95%');
  assert.ok(rBudget.regenerationCalls === 18 && rBudget.regenerationFlops > 0 && rBudget.reconstructionBytes > 0);
}
console.log('[pass] float64 serialization and weight-free self-bootstrapped neural regeneration checks');

// 5. Subprocess worker parity (--propose, --regenerate, --score)
{
  const workerPath = fileURLToPath(new URL('./worker.mjs', import.meta.url));
  const phi = Array.from({ length: PARAM_COUNT }, (_, i) => Math.sin(i * 0.4) * 0.15);
  const art = serialize(phi, 'secant_qn_trust');

  // --propose (serialization)
  const pSer = spawnSync(process.execPath, [workerPath, '--propose'], {
    input: JSON.stringify({
      targetArtifact: art,
      proposerArtifact: art,
      historyArtifact: null,
      family: 'anisotropic_gated_mlp',
      supportSeed: 700,
      supportCount: 3,
      arm: 'evolving_ser_reset',
      innerSteps: 4,
      metaSteps: 3,
      metaObjectiveId: 'w-test',
      transmission: 'serialization',
    }),
    encoding: 'utf8',
  });
  assert.equal(pSer.status, 0, pSer.stderr);
  const wSer = JSON.parse(pSer.stdout);
  const dBud = counter();
  const dProp = proposeSuccessor({
    targetPhi: phi,
    proposerPhi: phi,
    rule: 'secant_qn_trust',
    arm: 'evolving_ser_reset',
    supportTasks: sampleTasks('anisotropic_gated_mlp', 700, 3),
    innerSteps: 4,
    metaSteps: 3,
    metaObjectiveId: 'w-test',
    initialHistory: null,
  }, dBud);
  assert.equal(wSer.childArtifact, serialize(dProp.theta, 'secant_qn_trust'));
  assert.equal(wSer.budget.oracleCalls, dBud.oracleCalls);

  // --propose (neural_regen) -> --regenerate
  const pReg = spawnSync(process.execPath, [workerPath, '--propose'], {
    input: JSON.stringify({
      targetArtifact: art,
      proposerArtifact: art,
      historyArtifact: null,
      family: 'anisotropic_gated_mlp',
      supportSeed: 700,
      supportCount: 3,
      arm: 'evolving_regen_reset',
      innerSteps: 4,
      metaSteps: 3,
      metaObjectiveId: 'w-test',
      transmission: 'neural_regen',
    }),
    encoding: 'utf8',
  });
  assert.equal(pReg.status, 0, pReg.stderr);
  const wRegProp = JSON.parse(pReg.stdout);
  assert.equal(wRegProp.childArtifact, null, 'Neural regen proposal must emit null childArtifact');
  assert.ok(typeof wRegProp.transcript === 'string');

  // Verify --regenerate rejects smuggled childArtifact
  const smuggle = spawnSync(process.execPath, [workerPath, '--regenerate'], {
    input: JSON.stringify({ transcript: wRegProp.transcript, childArtifact: wSer.childArtifact }),
    encoding: 'utf8',
  });
  assert.notEqual(smuggle.status, 0, 'Worker --regenerate must reject smuggled childArtifact');

  const regRun = spawnSync(process.execPath, [workerPath, '--regenerate'], {
    input: JSON.stringify({ transcript: wRegProp.transcript, regenSteps: 12 }),
    encoding: 'utf8',
  });
  assert.equal(regRun.status, 0, regRun.stderr);
  const regOut = JSON.parse(regRun.stdout);
  assert.ok(regOut.finalBehavioralMse < regOut.initialBehavioralMse);

  // --score
  const scRun = spawnSync(process.execPath, [workerPath, '--score'], {
    input: JSON.stringify({
      artifact: regOut.regeneratedArtifact,
      family: 'anisotropic_gated_mlp',
      holdoutSeed: 800,
      holdoutCount: 4,
      innerSteps: 4,
    }),
    encoding: 'utf8',
  });
  assert.equal(scRun.status, 0, scRun.stderr);
  const scOut = JSON.parse(scRun.stdout);
  const directLosses = evaluateRule(
    reconstruct(regOut.regeneratedArtifact).phi,
    'secant_qn_trust',
    sampleTasks('anisotropic_gated_mlp', 800, 4),
    4,
    counter(),
  );
  assert.deepEqual(scOut.losses, directLosses);
}
console.log('[pass] clean OS subprocess worker exact parity (--propose, --regenerate, --score)');

// 6. Exact preprocessing oracle-call parity across learned init, SGD, Adam, and L-BFGS + statistical checks
{
  for (const family of FAMILIES) {
    const prep = initializeAndCalibrate({
      seed: 5555,
      family,
      rule: 'secant_qn_trust',
      config: {
        trainingCandidates: 3,
        trainingEnvironments: 2,
        trainSupportCount: 3,
        trainQueryCount: 3,
        trainInnerSteps: 4,
        trainMetaSteps: 3,
        sgdGrid: [[0.02, 0], [0.1, 0.8], [0.5, 0.8]],
        adamGrid: [[0.02, 0.5], [0.1, 0.5], [0.2, 0.9]],
        bfgsRates: [0.05, 0.3, 1.0],
      },
    });
    const q = prep.learnedBudget.oracleCalls;
    assert.ok(q > 0);
    assert.equal(prep.calibrations.sgd.budget.oracleCalls, q);
    assert.equal(prep.calibrations.adam.budget.oracleCalls, q);
    assert.equal(prep.calibrations.bfgs.budget.oracleCalls, q);
  }
  assert.equal(signProbability(12, 0), 1 / 4096);
  const s = summarizeEffects([0.05, 0.04, 0.03, 0.02, 0.02, 0.02, 0.015, 0.012, 0.011, 0.01, 0.005, -0.001], 1e-6);
  assert.equal(s.wins, 11);
  assert.equal(s.losses, 1);
}
console.log('[pass] exact training/calibration oracle parity and sign-test checks');
