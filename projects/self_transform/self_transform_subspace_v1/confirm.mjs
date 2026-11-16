import fs from 'node:fs';
import { spawnSync } from 'node:child_process';
import { performance } from 'node:perf_hooks';
import { fileURLToPath } from 'node:url';
import assert from 'node:assert/strict';
import {
  counter,
  freezeState,
  reconstruct,
  restoreState,
  serialize,
  sha256,
} from './operator.mjs';
import {
  evaluateRule,
  initializeAndCalibrate,
  makeEnvironment,
  mean,
  proposeSuccessor,
  sampleTasks,
  subspaceOverlap,
} from './tasks.mjs';
import { analyzeConfirmation } from './stats.mjs';

const here = new URL('.', import.meta.url);
const workerPath = fileURLToPath(new URL('./worker.mjs', here));
const protocol = JSON.parse(fs.readFileSync(new URL('./protocol.confirmation.json', here), 'utf8'));
const outputPath = process.argv[2];
if (!outputPath) {
  throw new Error('Usage: node projects/self_transform_subspace_v1/confirm.mjs <new-local-receipt-path>');
}

// Verify sealed link to frozen Stage 1 selection receipt before any work
const selectionReceiptRaw = fs.readFileSync(protocol.selectionReceiptPath, 'utf8');
const actualSelectionSha = sha256(selectionReceiptRaw);
assert.equal(
  actualSelectionSha,
  protocol.selectionReceiptSha256,
  'Selection receipt SHA-256 does not match sealed confirmation protocol',
);
const selectionReceipt = JSON.parse(selectionReceiptRaw);
assert.equal(
  selectionReceipt.selectedRule,
  protocol.selectedRule,
  'Selected rule in confirmation protocol does not match Stage 1 selection winner',
);

const sourceFiles = ['observation.mjs', 'operator.mjs', 'tasks.mjs', 'worker.mjs', 'stats.mjs', 'confirm.mjs'];
const sourceHashes = Object.fromEntries(
  sourceFiles.map(name => [name, sha256(fs.readFileSync(new URL(name, here), 'utf8'))]),
);
const protocolHash = sha256(JSON.stringify(protocol));

fs.writeFileSync(
  `${outputPath}.protocol.json`,
  JSON.stringify({ protocol, protocolHash, sourceHashes }, null, 2),
  { flag: 'wx' },
);

function invokeWorker(mode, payload) {
  const proc = spawnSync(process.execPath, [workerPath, mode], {
    input: JSON.stringify(payload),
    encoding: 'utf8',
  });
  if (proc.status !== 0) {
    throw new Error(`Worker ${mode} failed: ${proc.stderr}`);
  }
  return JSON.parse(proc.stdout);
}

const started = performance.now();
const rule = protocol.selectedRule;
const preprocessingReceipts = [];
const records = [];
const pairedProposerRecords = [];

const reproductionSummary = {
  workerProposalCount: 0,
  workerScoreCount: 0,
  allWorkerRoundtripsExact: true,
  allDirectParityAuditsExact: true,
  serializationOnlyChecks: 0,
  serializationOnlyMaxAbsDrift: 0,
  auditBudgetScalarQueries: 0,
};

function isolatedScore({ artifact, env, envSeed, holdoutSeed, holdoutCount, family, innerSteps, innerProbeSeed, scoreCache }) {
  const cacheKey = `${artifact}|${envSeed}|${holdoutSeed}|${holdoutCount}|${family}|${innerSteps}|${innerProbeSeed}`;
  if (scoreCache && scoreCache.has(cacheKey)) {
    return scoreCache.get(cacheKey);
  }
  const workerRes = invokeWorker('--score', {
    artifact,
    envSeed,
    holdoutSeed,
    holdoutCount,
    family,
    innerSteps,
    innerProbeSeed,
  });
  reproductionSummary.workerScoreCount += 1;
  if (workerRes.reconstructedArtifact !== artifact) {
    reproductionSummary.allWorkerRoundtripsExact = false;
    throw new Error('Worker score artifact roundtrip mismatch');
  }

  // Direct in-process parity audit (tracked separately; never added to search/adaptation budget)
  const auditBudget = counter();
  const tasks = sampleTasks(env, holdoutSeed, holdoutCount, family);
  const directLosses = evaluateRule(reconstruct(artifact).phi, rule, tasks, innerSteps, innerProbeSeed, auditBudget);
  reproductionSummary.auditBudgetScalarQueries += auditBudget.scalarQueries;
  try {
    assert.deepEqual(workerRes.losses, directLosses);
  } catch (err) {
    reproductionSummary.allDirectParityAuditsExact = false;
    throw err;
  }

  const out = { losses: workerRes.losses, meanLoss: mean(workerRes.losses), budget: workerRes.budget };
  if (scoreCache) scoreCache.set(cacheKey, out);
  return out;
}

function isolatedPropose({
  targetArtifact,
  proposerArtifact,
  historyArtifact,
  env,
  envSeed,
  supportSeed,
  supportCount,
  family,
  arm,
  innerSteps,
  metaSteps,
  metaObjectiveId,
  probeBaseSeed,
  innerProbeSeed,
  settings,
}) {
  const workerRes = invokeWorker('--propose', {
    targetArtifact,
    proposerArtifact,
    historyArtifact,
    envSeed,
    supportSeed,
    supportCount,
    family,
    arm,
    innerSteps,
    metaSteps,
    metaObjectiveId,
    probeBaseSeed,
    innerProbeSeed,
    settings,
  });
  reproductionSummary.workerProposalCount += 1;

  // Verify roundtrip integrity
  const recChild = reconstruct(workerRes.childArtifact);
  if (serialize(recChild.phi, recChild.rule) !== workerRes.childArtifact) {
    reproductionSummary.allWorkerRoundtripsExact = false;
    throw new Error('Child artifact reserialization mismatch');
  }
  if (workerRes.historyArtifact !== null) {
    const recHist = restoreState(workerRes.historyArtifact);
    if (freezeState(recHist) !== workerRes.historyArtifact) {
      reproductionSummary.allWorkerRoundtripsExact = false;
      throw new Error('History artifact reserialization mismatch');
    }
  }

  // Direct in-process parity audit
  const auditBudget = counter();
  const supportTasks = sampleTasks(env, supportSeed, supportCount, family);
  const directOut = proposeSuccessor({
    targetPhi: reconstruct(targetArtifact).phi,
    proposerPhi: reconstruct(proposerArtifact).phi,
    rule,
    arm,
    supportTasks,
    innerSteps,
    metaSteps,
    metaObjectiveId,
    probeBaseSeed,
    innerProbeSeed,
    initialHistory: historyArtifact ? restoreState(historyArtifact) : null,
    settings,
  }, auditBudget);
  reproductionSummary.auditBudgetScalarQueries += auditBudget.scalarQueries;

  const expectedChildArt = serialize(directOut.theta, rule);
  const expectedHistArt = directOut.history ? freezeState(directOut.history) : null;
  if (workerRes.childArtifact !== expectedChildArt || workerRes.historyArtifact !== expectedHistArt) {
    reproductionSummary.allDirectParityAuditsExact = false;
    throw new Error(`Direct parity audit mismatch in ${arm}`);
  }

  return workerRes;
}

for (const family of protocol.families) {
  for (const seed of protocol.seeds) {
    const prepStart = performance.now();
    const prep = initializeAndCalibrate({
      seed,
      family,
      rule,
      config: protocol.preprocessing,
    });
    assert.equal(prep.learnedBudget.scalarQueries, prep.calibrations.spsa.budget.scalarQueries);
    assert.equal(prep.learnedBudget.scalarQueries, prep.calibrations.adam.budget.scalarQueries);
    assert.equal(prep.learnedBudget.scalarQueries, prep.calibrations.bfgs.budget.scalarQueries);

    preprocessingReceipts.push({
      family,
      seed,
      selectedInitCandidate: prep.selectedCandidate,
      initialFitness: prep.initialFitness,
      perMethodScalarQueries: prep.learnedBudget.scalarQueries,
      sharedChargedScalarQueries: prep.sharedChargedScalarQueries,
      calibrated: {
        spsa: { rate: prep.calibrations.spsa.selected.rate },
        adam: { rate: prep.calibrations.adam.selected.rate, beta: prep.calibrations.adam.selected.beta },
        bfgs: { rate: prep.calibrations.bfgs.selected.rate },
      },
      prepMs: performance.now() - prepStart,
    });

    const envSeed = seed + 50000;
    const supportSeed = seed + 51000;
    const evalEnv = makeEnvironment(envSeed);
    const initialArtifact = serialize(prep.initialPhi, rule);
    const initialOverlap = subspaceOverlap(prep.initialPhi, rule, evalEnv);
    const metaObjectiveId = `conf/${family}/${seed}`;

    const chainStates = Object.fromEntries(
      protocol.arms.map(arm => [arm, { artifact: initialArtifact, historyArtifact: null }]),
    );

    const scoreCache = new Map();

    for (let gen = 0; gen < protocol.generations; gen += 1) {
      const holdoutSeed = seed + 60000 + gen * 100;
      const innerProbeSeed = seed + 80000 + gen * 500;
      const probeBaseSeed = seed + 70000 + gen * 500;
      const genProposals = [];

      for (const arm of protocol.arms) {
        const current = chainStates[arm];
        const retainsHistory = arm.endsWith('_retain');
        const historyIn = retainsHistory ? current.historyArtifact : null;
        const proposerArtifact = (arm === 'fixed_reset' || arm === 'fixed_retain')
          ? initialArtifact
          : current.artifact;

        const settings = arm.includes('spsa') ? prep.calibrations.spsa.selected
          : arm.includes('adam') ? prep.calibrations.adam.selected
            : arm.includes('bfgs') ? prep.calibrations.bfgs.selected : {};

        const propStart = performance.now();
        const propRes = isolatedPropose({
          targetArtifact: current.artifact,
          proposerArtifact,
          historyArtifact: historyIn,
          env: evalEnv,
          envSeed,
          supportSeed,
          supportCount: protocol.metaSupportTasks,
          family,
          arm,
          innerSteps: protocol.innerSteps,
          metaSteps: protocol.metaStepsPerGeneration,
          metaObjectiveId,
          probeBaseSeed,
          innerProbeSeed,
          settings,
        });
        genProposals.push({
          arm,
          parentArtifact: current.artifact,
          childArtifact: propRes.childArtifact,
          nextHistoryArtifact: retainsHistory ? propRes.historyArtifact : null,
          proposalBudget: propRes.budget,
          outerBudget: propRes.outerBudget,
          proposalMs: performance.now() - propStart,
        });
      }

      // Score all frozen parent and child artifacts on fresh held-out tasks (never exposed to proposals)
      for (const p of genProposals) {
        const useCache = p.arm !== 'serialization_only';
        const parentScore = isolatedScore({
          artifact: p.parentArtifact,
          env: evalEnv,
          envSeed,
          holdoutSeed,
          holdoutCount: protocol.holdoutTasksPerGeneration,
          family,
          innerSteps: protocol.innerSteps,
          innerProbeSeed: seed + 90000 + gen * 500,
          scoreCache: useCache ? scoreCache : null,
        });
        const childScore = isolatedScore({
          artifact: p.childArtifact,
          env: evalEnv,
          envSeed,
          holdoutSeed,
          holdoutCount: protocol.holdoutTasksPerGeneration,
          family,
          innerSteps: protocol.innerSteps,
          innerProbeSeed: seed + 90000 + gen * 500,
          scoreCache: useCache ? scoreCache : null,
        });

        if (p.arm === 'serialization_only') {
          reproductionSummary.serializationOnlyChecks += 1;
          const drift = Math.abs(childScore.meanLoss - parentScore.meanLoss);
          reproductionSummary.serializationOnlyMaxAbsDrift = Math.max(
            reproductionSummary.serializationOnlyMaxAbsDrift,
            drift,
          );
        }

        const childPhi = reconstruct(p.childArtifact).phi;
        records.push({
          family,
          seed,
          generation: gen,
          arm: p.arm,
          parentMean: parentScore.meanLoss,
          childMean: childScore.meanLoss,
          initialOverlap,
          childOverlap: subspaceOverlap(childPhi, rule, evalEnv),
          proposalScalarQueries: p.proposalBudget.scalarQueries,
          outerMetaScalarQueries: p.outerBudget.scalarQueries,
          scoreScalarQueries: childScore.budget.scalarQueries,
          proposalMs: p.proposalMs,
        });

        chainStates[p.arm] = {
          artifact: p.childArtifact,
          historyArtifact: p.nextHistoryArtifact,
        };
      }
    }

    // Direct same-parent paired proposer split from final evolved hereditary_reset artifact (history = null)
    const sharedParentArtifact = chainStates.hereditary_reset.artifact;
    const pairedSupportSeed = seed + 55000;
    const pairedHoldoutSeed = seed + 65000;
    const pairedMetaObjId = `paired/${family}/${seed}`;
    const pairedSpecs = [
      { arm: 'paired_self', proposerArtifact: sharedParentArtifact, underlyingArm: 'hereditary_reset', settings: {} },
      { arm: 'paired_fixed', proposerArtifact: initialArtifact, underlyingArm: 'fixed_reset', settings: {} },
      { arm: 'paired_parent_unchanged', proposerArtifact: sharedParentArtifact, underlyingArm: 'serialization_only', settings: {} },
      { arm: 'paired_spsa', proposerArtifact: sharedParentArtifact, underlyingArm: 'tuned_spsa_reset', settings: prep.calibrations.spsa.selected },
      { arm: 'paired_adam', proposerArtifact: sharedParentArtifact, underlyingArm: 'tuned_adam_reset', settings: prep.calibrations.adam.selected },
      { arm: 'paired_bfgs', proposerArtifact: sharedParentArtifact, underlyingArm: 'tuned_bfgs_reset', settings: prep.calibrations.bfgs.selected },
    ];

    for (const sp of pairedSpecs) {
      const propRes = isolatedPropose({
        targetArtifact: sharedParentArtifact,
        proposerArtifact: sp.proposerArtifact,
        historyArtifact: null,
        env: evalEnv,
        envSeed,
        supportSeed: pairedSupportSeed,
        supportCount: protocol.metaSupportTasks,
        family,
        arm: sp.underlyingArm,
        innerSteps: protocol.innerSteps,
        metaSteps: protocol.metaStepsPerGeneration,
        metaObjectiveId: pairedMetaObjId,
        probeBaseSeed: seed + 75000,
        innerProbeSeed: seed + 85000,
        settings: sp.settings,
      });
      const sc = isolatedScore({
        artifact: propRes.childArtifact,
        env: evalEnv,
        envSeed,
        holdoutSeed: pairedHoldoutSeed,
        holdoutCount: protocol.holdoutTasksPerGeneration,
        family,
        innerSteps: protocol.innerSteps,
        innerProbeSeed: seed + 95000,
        scoreCache,
      });
      pairedProposerRecords.push({
        family,
        seed,
        arm: sp.arm,
        holdoutMean: sc.meanLoss,
        overlap: subspaceOverlap(reconstruct(propRes.childArtifact).phi, rule, evalEnv),
        proposalScalarQueries: propRes.budget.scalarQueries,
      });
    }
  }
}

const receipt = {
  protocol,
  protocolHash,
  sourceHashes,
  reproductionSummary,
  preprocessingReceipts,
  records,
  pairedProposerRecords,
  elapsedMs: performance.now() - started,
  node: process.version,
};

receipt.analysis = analyzeConfirmation(receipt);
fs.writeFileSync(outputPath, JSON.stringify(receipt, null, 2), { flag: 'wx' });
console.log(JSON.stringify({
  elapsedMs: receipt.elapsedMs,
  selectedRule: protocol.selectedRule,
  reproductionGate: receipt.analysis.reproductionGate,
  families: Object.fromEntries(
    Object.entries(receipt.analysis.families).map(([fam, f]) => [fam, {
      parentToChildTransitions: f.parentToChildTransitions,
      subspaceAlignment: f.subspaceAlignment,
      retainedAdaptation: {
        passes: f.gates.retainedAdaptation.passes,
        wins: f.gates.retainedAdaptation.summary.wins,
        losses: f.gates.retainedAdaptation.summary.losses,
        medianRel: f.gates.retainedAdaptation.summary.median,
        signP: f.gates.retainedAdaptation.summary.oneSidedSignP,
      },
      proposerChainRuleOnly: {
        passes: f.gates.proposerChainRuleOnly.passes,
        wins: f.gates.proposerChainRuleOnly.summary.wins,
        losses: f.gates.proposerChainRuleOnly.summary.losses,
        medianRel: f.gates.proposerChainRuleOnly.summary.median,
        signP: f.gates.proposerChainRuleOnly.summary.oneSidedSignP,
      },
      pairedSameParentProposer: {
        passes: f.gates.pairedSameParentProposer.passesPracticalAndSign,
        wins: f.gates.pairedSameParentProposer.summary.wins,
        losses: f.gates.pairedSameParentProposer.summary.losses,
        medianRel: f.gates.pairedSameParentProposer.summary.median,
        signP: f.gates.pairedSameParentProposer.summary.oneSidedSignP,
      },
      conventionalAllPass: f.gates.conventionalAllPass,
      conventional: Object.fromEntries(
        Object.entries(f.gates.conventional).map(([k, g]) => [k, {
          passes: g.passes,
          wins: g.summary.wins,
          losses: g.summary.losses,
          medianRel: g.summary.median,
          signP: g.summary.oneSidedSignP,
        }]),
      ),
      factorialAttribution: {
        memoryWithinFixedMedian: f.factorialAttribution.memoryEffectWithinFixed.median,
        memoryWithinHereditaryMedian: f.factorialAttribution.memoryEffectWithinHereditary.median,
        ruleWithinRetainedMemoryMedian: f.factorialAttribution.ruleEffectWithinRetainedMemory.median,
      },
    }]),
  ),
}, null, 2));
