import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { observationWindow } from './observation.mjs';
import {
  BLOCK_WIDTH,
  CANDIDATE_RULES,
  PARAM_COUNT,
  counter,
  freezeState,
  reconstruct,
  restoreState,
  serialize,
  step,
} from './operator.mjs';
import {
  FAMILIES,
  evaluateRule,
  initializeAndCalibrate,
  makeEnvironment,
  mean,
  proposeSuccessor,
  sampleTasks,
} from './tasks.mjs';
import { signProbability, summarizeEffects } from './stats.mjs';

// 1. Observation window hard query cap, deep-copy isolation, and failed-query charging
{
  const prev = { objectiveId: 'obj-1', dimension: 4, t: 2, vec: [1, 2, 3, 4] };
  const win = observationWindow({
    objectiveId: 'obj-1',
    theta: [0, 0, 0, 0],
    previous: prev,
    loss: pt => pt.reduce((s, x) => s + x * x, 0),
    limit: 8,
  });
  prev.vec[0] = 999;
  assert.equal(win.history.vec[0], 1, 'History must be deep-cloned');
  for (let i = 0; i < 8; i += 1) {
    assert.equal(win.query([1, 0, 0, 0]), 1);
  }
  assert.equal(win.receipt().scalarQueries, 8);
  assert.throws(() => win.query([0, 0, 0, 0]), /exhausted/);
  assert.throws(() => observationWindow({
    objectiveId: 'obj-2', theta: [0, 0, 0, 0], previous: prev, loss: () => 0,
  }), /mismatch/);
  assert.throws(() => observationWindow({
    objectiveId: 'obj-1', theta: [0, 0], previous: prev, loss: () => 0,
  }), /mismatch/);

  const badWin = observationWindow({ objectiveId: 'bad', theta: [0, 0], loss: () => NaN });
  assert.throws(() => badWin.query([0, 0]), /Non-finite/);
  assert.equal(badWin.receipt().scalarQueries, 1, 'Failed query must consume budget');
}
console.log('[pass] observationWindow budget, isolation, and failure-charging invariants');

// 2. Artifact serialization, negative-zero fidelity, and corruption rejection
{
  const phi = Array.from({ length: PARAM_COUNT }, (_, i) => (i === 0 ? -0 : (i - 20) * 0.125));
  for (const rule of CANDIDATE_RULES) {
    const text = serialize(phi, rule);
    const rec = reconstruct(text);
    assert.equal(rec.rule, rule);
    assert.ok(Object.is(rec.phi[0], -0), 'Must preserve IEEE-754 -0');
    assert.deepEqual(rec.phi.slice(1), phi.slice(1));
    assert.equal(serialize(rec.phi, rec.rule), text);

    const parsed = JSON.parse(text);
    parsed.weightsHex = `ff${parsed.weightsHex.slice(2)}`;
    assert.throws(() => reconstruct(JSON.stringify(parsed)), /SHA-256 mismatch/);
  }
  assert.throws(() => serialize(Array(PARAM_COUNT).fill(Infinity)), /finite/);
  const st = { objectiveId: 'meta', dimension: 16, t: 1, arr: [-0, 1.5, -2.25] };
  const restored = restoreState(freezeState(st));
  assert.ok(Object.is(restored.arr[0], -0));
  assert.deepEqual(restored, st);
}
console.log('[pass] exact float64 artifact and state serialization checks');

// 3. Exact 8-query parity, zero-signal identity, scale homogeneity, and multi-block closure (M=1, 2, 3)
{
  const phi = Array.from({ length: PARAM_COUNT }, (_, i) => Math.sin(i + 1) * 0.3);
  for (const blocks of [1, 2, 3]) {
    const D = blocks * BLOCK_WIDTH;
    const theta0 = Array.from({ length: D }, (_, i) => Math.cos(i) * 0.25);
    const quadLoss = x => x.reduce((s, v, i) => s + ((i % 5) + 1) * v * v, 0);

    for (const rule of CANDIDATE_RULES) {
      const b1 = counter();
      const out1 = step({
        theta: theta0, phi, rule, method: 'learned', objectiveId: `m${blocks}`,
        loss: quadLoss, probeSeed: 77, stepIndex: 0,
      }, b1);
      assert.equal(b1.scalarQueries, 8);
      assert.equal(b1.updates, 1);

      // Positive objective scale homogeneity: L(x) vs 1000 * L(x) vs 0.001 * L(x)
      const bBig = counter();
      const outBig = step({
        theta: theta0, phi, rule, method: 'learned', objectiveId: `m${blocks}`,
        loss: x => 1000 * quadLoss(x), probeSeed: 77, stepIndex: 0,
      }, bBig);
      const bSmall = counter();
      const outSmall = step({
        theta: theta0, phi, rule, method: 'learned', objectiveId: `m${blocks}`,
        loss: x => 0.001 * quadLoss(x), probeSeed: 77, stepIndex: 0,
      }, bSmall);
      for (let i = 0; i < D; i += 1) {
        assert.ok(Math.abs(out1.theta[i] - outBig.theta[i]) < 1e-7, `Scale +1e3 homogeneity drift at ${i}`);
        assert.ok(Math.abs(out1.theta[i] - outSmall.theta[i]) < 1e-6, `Scale 1e-3 homogeneity drift at ${i}`);
      }

      // Constant loss -> exact zero displacement
      const flatOut = step({
        theta: theta0, phi, rule, method: 'learned', objectiveId: `flat${blocks}`,
        loss: () => 3.14159, probeSeed: 77, stepIndex: 0,
      }, counter());
      assert.deepEqual(flatOut.theta, theta0);
    }

    for (const method of ['spsa', 'adam', 'bfgs']) {
      const bc = counter();
      const outC = step({
        theta: theta0, method, rate: 0.1, beta: 0.9, objectiveId: `conv${blocks}`,
        loss: quadLoss, probeSeed: 77,
      }, bc);
      assert.equal(bc.scalarQueries, 8);
      assert.equal(outC.theta.length, D);
    }
  }
}
console.log('[pass] 8-query parity, objective scale homogeneity, zero-signal identity, and M=1/2/3 closure');

// 4. Clean subprocess worker parity (--propose and --score) vs direct in-process execution
{
  const workerPath = fileURLToPath(new URL('./worker.mjs', import.meta.url));
  const phi = Array.from({ length: PARAM_COUNT }, (_, i) => Math.sin(i * 0.7) * 0.2);
  const art = serialize(phi, 'block_subspace_2mode');

  const envSeed = 9100;
  const supportSeed = 9200;
  const holdoutSeed = 9300;
  const propRes = spawnSync(process.execPath, [workerPath, '--propose'], {
    input: JSON.stringify({
      targetArtifact: art,
      proposerArtifact: art,
      historyArtifact: null,
      envSeed,
      supportSeed,
      supportCount: 2,
      family: 'gated_bilinear',
      arm: 'hereditary_reset',
      innerSteps: 3,
      metaSteps: 3,
      metaObjectiveId: 'worker-test',
      probeBaseSeed: 400,
      innerProbeSeed: 800,
    }),
    encoding: 'utf8',
  });
  assert.equal(propRes.status, 0, propRes.stderr);
  const workerProp = JSON.parse(propRes.stdout);

  const directBudget = counter();
  const env = makeEnvironment(envSeed);
  const directProp = proposeSuccessor({
    targetPhi: phi,
    proposerPhi: phi,
    rule: 'block_subspace_2mode',
    arm: 'hereditary_reset',
    supportTasks: sampleTasks(env, supportSeed, 2, 'gated_bilinear'),
    innerSteps: 3,
    metaSteps: 3,
    metaObjectiveId: 'worker-test',
    probeBaseSeed: 400,
    innerProbeSeed: 800,
    initialHistory: null,
  }, directBudget);
  assert.equal(workerProp.childArtifact, serialize(directProp.theta, 'block_subspace_2mode'));
  assert.equal(workerProp.budget.scalarQueries, directBudget.scalarQueries);

  const scoreRes = spawnSync(process.execPath, [workerPath, '--score'], {
    input: JSON.stringify({
      artifact: workerProp.childArtifact,
      envSeed,
      holdoutSeed,
      holdoutCount: 4,
      family: 'gated_bilinear',
      innerSteps: 3,
      innerProbeSeed: 900,
    }),
    encoding: 'utf8',
  });
  assert.equal(scoreRes.status, 0, scoreRes.stderr);
  const workerScore = JSON.parse(scoreRes.stdout);
  const directScoreBudget = counter();
  const directLosses = evaluateRule(
    directProp.theta,
    'block_subspace_2mode',
    sampleTasks(env, holdoutSeed, 4, 'gated_bilinear'),
    3,
    900,
    directScoreBudget,
  );
  assert.deepEqual(workerScore.losses, directLosses);
  assert.equal(workerScore.budget.scalarQueries, directScoreBudget.scalarQueries);
}
console.log('[pass] clean OS subprocess worker exact parity (--propose and --score)');

// 5. Exact initialization vs conventional calibration budget equality across both task families
{
  for (const family of FAMILIES) {
    const prep = initializeAndCalibrate({
      seed: 12345,
      family,
      rule: 'block_subspace_2mode',
      config: {
        trainingCandidates: 3,
        trainingEnvironments: 2,
        trainSupportCount: 2,
        trainQueryCount: 2,
        trainInnerSteps: 3,
        trainMetaSteps: 3,
        spsaRates: [0.05, 0.5, 2.0],
        adamGrid: [[0.05, 0.0], [0.2, 0.5], [1.0, 0.9]],
        bfgsRates: [0.05, 0.5, 2.0],
      },
    });
    const qLearned = prep.learnedBudget.scalarQueries;
    assert.ok(qLearned > 0);
    assert.equal(prep.calibrations.spsa.budget.scalarQueries, qLearned);
    assert.equal(prep.calibrations.adam.budget.scalarQueries, qLearned);
    assert.equal(prep.calibrations.bfgs.budget.scalarQueries, qLearned);
    assert.equal(prep.sharedChargedScalarQueries, 4 * qLearned);
    assert.ok(Number.isFinite(mean([prep.initialFitness])));
  }
}
console.log('[pass] exact scalar-query budget parity between learned init and SPSA/Adam/L-BFGS calibration');

// 6. Statistical sign test and order-statistic summary checks
{
  assert.equal(signProbability(12, 0), 1 / 4096);
  assert.equal(signProbability(10, 2), (1 + 12 + 66) / 4096);
  assert.equal(signProbability(0, 0), 1);
  const eff = [0.05, 0.04, 0.03, 0.02, 0.015, 0.012, 0.011, 0.009, 0.008, 0.005, 0.0, -0.002];
  const sum = summarizeEffects(eff, 1e-6);
  assert.equal(sum.wins, 10);
  assert.equal(sum.losses, 1);
  assert.equal(sum.ties, 1);
  assert.equal(sum.oneSidedSignP, signProbability(10, 1));
  assert.ok(sum.median > 0.01);
  assert.ok(sum.medianOrderStatisticInterval.low <= sum.median);
  assert.ok(sum.medianOrderStatisticInterval.high >= sum.median);
}
console.log('[pass] exact binomial sign-test and 12-seed median order-statistic checks');
