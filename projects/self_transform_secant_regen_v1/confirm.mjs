import fs from 'node:fs';
import { spawnSync } from 'node:child_process';
import { performance } from 'node:perf_hooks';
import { fileURLToPath } from 'node:url';
import assert from 'node:assert/strict';
import { counter } from './observation.mjs';
import {
  freezeState,
  parseBehavioralTranscript,
  reconstruct,
  regenerateFromTranscript,
  restoreState,
  serialize,
  sha256,
} from './operator.mjs';
import {
  evaluateRule,
  initializeAndCalibrate,
  mean,
  proposeSuccessor,
  sampleTasks,
} from './tasks.mjs';
import { analyzeConfirmation } from './stats.mjs';

const here = new URL('.', import.meta.url);
const workerPath = fileURLToPath(new URL('./worker.mjs', here));
const protocol = JSON.parse(fs.readFileSync(new URL('./protocol.confirmation.json', here), 'utf8'));
const outputPath = process.argv[2];
if (!outputPath) {
  throw new Error('Usage: node projects/self_transform_secant_regen_v1/confirm.mjs <new-receipt-path>');
}

// Verify sealed cryptographic link to Stage 1 selection receipt before any computation
const selectionRaw = fs.readFileSync(protocol.selectionReceiptPath, 'utf8');
assert.equal(
  sha256(selectionRaw),
  protocol.selectionReceiptSha256,
  'Stage 1 selection receipt SHA-256 mismatch',
);
const selectionReceipt = JSON.parse(selectionRaw);
assert.equal(selectionReceipt.selectedRule, protocol.selectedRule, 'Selected rule mismatch vs Stage 1 winner');

const sourceFiles = ['observation.mjs', 'autodiff.mjs', 'operator.mjs', 'tasks.mjs', 'worker.mjs', 'stats.mjs', 'confirm.mjs'];
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
const pairedRecords = [];

const reproductionSummary = {
  workerProposalCount: 0,
  workerRegenerationCount: 0,
  workerScoreCount: 0,
  allWorkerRoundtripsExact: true,
  allDirectParityAuditsExact: true,
  allRegenerationWeightFree: true,
  serializationOnlyChecks: 0,
  serializationOnlyMaxAbsDrift: 0,
  auditOracleCalls: 0,
  stage1SelectionOracleCallsCharged: selectionReceipt.totalSelectionOracleCalls,
};

function isolatedScore({ artifact, family, holdoutSeed, holdoutCount, innerSteps, scoreCache }) {
  const key = `${artifact}|${family}|${holdoutSeed}|${holdoutCount}|${innerSteps}`;
  if (scoreCache && scoreCache.has(key)) return scoreCache.get(key);

  const wRes = invokeWorker('--score', { artifact, family, holdoutSeed, holdoutCount, innerSteps });
  reproductionSummary.workerScoreCount += 1;
  if (wRes.reconstructedArtifact !== artifact) {
    reproductionSummary.allWorkerRoundtripsExact = false;
    throw new Error('Worker score artifact roundtrip mismatch');
  }

  const auditBudget = counter();
  const tasks = sampleTasks(family, holdoutSeed, holdoutCount);
  const directLosses = evaluateRule(reconstruct(artifact).phi, rule, tasks, innerSteps, auditBudget);
  reproductionSummary.auditOracleCalls += auditBudget.oracleCalls;
  try {
    assert.deepEqual(wRes.losses, directLosses);
  } catch (err) {
    reproductionSummary.allDirectParityAuditsExact = false;
    throw err;
  }

  const out = { losses: wRes.losses, meanLoss: mean(wRes.losses), budget: wRes.budget };
  if (scoreCache) scoreCache.set(key, out);
  return out;
}

function isolatedProposeAndReconstruct({
  targetArtifact,
  proposerArtifact,
  historyArtifact,
  family,
  supportSeed,
  supportCount,
  arm,
  innerSteps,
  metaSteps,
  metaObjectiveId,
  settings,
  transmission,
  regenSteps,
  transcriptProbes,
  transcriptSeed,
}) {
  const wProp = invokeWorker('--propose', {
    targetArtifact,
    proposerArtifact,
    historyArtifact,
    family,
    supportSeed,
    supportCount,
    arm,
    innerSteps,
    metaSteps,
    metaObjectiveId,
    settings,
    transmission,
    transcriptProbes,
    transcriptSeed,
  });
  reproductionSummary.workerProposalCount += 1;

  // Direct in-process proposal parity audit
  const auditBudget = counter();
  const directOut = proposeSuccessor({
    targetPhi: reconstruct(targetArtifact).phi,
    proposerPhi: reconstruct(proposerArtifact).phi,
    rule,
    arm,
    supportTasks: sampleTasks(family, supportSeed, supportCount),
    innerSteps,
    metaSteps,
    metaObjectiveId,
    initialHistory: historyArtifact ? restoreState(historyArtifact) : null,
    settings,
    emitTranscript: transmission === 'neural_regen',
    transcriptProbes,
    transcriptSeed,
  }, auditBudget);
  reproductionSummary.auditOracleCalls += auditBudget.oracleCalls;

  const expectedHist = directOut.history ? freezeState(directOut.history) : null;
  if (wProp.historyArtifact !== expectedHist) {
    reproductionSummary.allDirectParityAuditsExact = false;
    throw new Error(`History parity mismatch in ${arm}`);
  }

  if (transmission === 'serialization') {
    const expectedArt = serialize(directOut.theta, rule);
    if (wProp.childArtifact !== expectedArt) {
      reproductionSummary.allDirectParityAuditsExact = false;
      throw new Error(`Child serialization parity mismatch in ${arm}`);
    }
    const recChild = reconstruct(wProp.childArtifact);
    if (serialize(recChild.phi, recChild.rule) !== wProp.childArtifact) {
      reproductionSummary.allWorkerRoundtripsExact = false;
      throw new Error('Child reserialization mismatch');
    }
    return {
      childArtifact: wProp.childArtifact,
      historyArtifact: wProp.historyArtifact,
      proposalBudget: wProp.budget,
      regenBudget: counter(),
      regenInitialMse: 0,
      regenFinalMse: 0,
    };
  }

  // Weight-free behavioral neural regeneration in a SECOND clean OS subprocess!
  if (wProp.childArtifact !== null || typeof wProp.transcript !== 'string' || wProp.transcript.includes('weightsHex')) {
    reproductionSummary.allRegenerationWeightFree = false;
    throw new Error('Weight leakage detected on neural_regen channel');
  }
  parseBehavioralTranscript(wProp.transcript);
  if (wProp.transcript !== directOut.transcript) {
    reproductionSummary.allDirectParityAuditsExact = false;
    throw new Error('Behavioral transcript parity mismatch');
  }

  const wRegen = invokeWorker('--regenerate', {
    transcript: wProp.transcript,
    regenSteps,
  });
  reproductionSummary.workerRegenerationCount += 1;

  // Direct regeneration parity audit
  const auditRegenBudget = counter();
  const directRegen = regenerateFromTranscript(wProp.transcript, regenSteps, auditRegenBudget);
  reproductionSummary.auditOracleCalls += auditRegenBudget.regenerationCalls;
  if (wRegen.regeneratedArtifact !== serialize(directRegen.phi, rule)) {
    reproductionSummary.allDirectParityAuditsExact = false;
    throw new Error('Neural regeneration subprocess parity mismatch');
  }

  return {
    childArtifact: wRegen.regeneratedArtifact,
    historyArtifact: wProp.historyArtifact,
    proposalBudget: wProp.budget,
    regenBudget: wRegen.budget,
    regenInitialMse: wRegen.initialBehavioralMse,
    regenFinalMse: wRegen.finalBehavioralMse,
  };
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
    assert.equal(prep.learnedBudget.oracleCalls, prep.calibrations.sgd.budget.oracleCalls);
    assert.equal(prep.learnedBudget.oracleCalls, prep.calibrations.adam.budget.oracleCalls);
    assert.equal(prep.learnedBudget.oracleCalls, prep.calibrations.bfgs.budget.oracleCalls);

    preprocessingReceipts.push({
      family,
      seed,
      selectedInitCandidate: prep.selectedCandidate,
      initialFitness: prep.initialFitness,
      perMethodOracleCalls: prep.learnedBudget.oracleCalls,
      sharedChargedOracleCalls: prep.sharedChargedOracleCalls,
      calibrated: {
        sgd: { rate: prep.calibrations.sgd.selected.rate, beta: prep.calibrations.sgd.selected.beta },
        adam: { rate: prep.calibrations.adam.selected.rate, beta: prep.calibrations.adam.selected.beta },
        bfgs: { rate: prep.calibrations.bfgs.selected.rate },
      },
      prepMs: performance.now() - prepStart,
    });

    const initialArtifact = serialize(prep.initialPhi, rule);
    const metaObjectiveId = `conf/${family}/${seed}`;
    const chainStates = Object.fromEntries(
      protocol.arms.map(arm => [arm, { artifact: initialArtifact, historyArtifact: null }]),
    );
    const scoreCache = new Map();

    for (let gen = 0; gen < protocol.generations; gen += 1) {
      const supportSeed = seed + 51000 + gen * 200;
      const holdoutSeed = seed + 60000 + gen * 200;
      const genProposals = [];

      for (const arm of protocol.arms) {
        const current = chainStates[arm];
        const retainsHistory = arm.endsWith('_retain');
        const historyIn = retainsHistory ? current.historyArtifact : null;
        const proposerArtifact = (arm === 'fixed_ser_reset' || arm === 'fixed_ser_retain')
          ? initialArtifact
          : current.artifact;
        const isRegen = arm.includes('_regen_');
        const isBudgetMatchedRegen = arm === 'evolving_regen_budget_matched';

        const metaSteps = isBudgetMatchedRegen
          ? protocol.budgetMatchedRegen.metaStepsPerGeneration
          : protocol.metaStepsPerGeneration;
        const regenSteps = isBudgetMatchedRegen
          ? protocol.budgetMatchedRegen.regenSteps
          : protocol.neuralRegeneration.regenSteps;

        const settings = arm.includes('sgd') ? prep.calibrations.sgd.selected
          : arm.includes('adam') ? prep.calibrations.adam.selected
            : arm.includes('bfgs') ? prep.calibrations.bfgs.selected : {};

        const propStart = performance.now();
        const propRes = isolatedProposeAndReconstruct({
          targetArtifact: current.artifact,
          proposerArtifact,
          historyArtifact: historyIn,
          family,
          supportSeed,
          supportCount: protocol.metaSupportTasks,
          arm,
          innerSteps: protocol.innerSteps,
          metaSteps,
          metaObjectiveId,
          settings,
          transmission: isRegen ? 'neural_regen' : 'serialization',
          regenSteps,
          transcriptProbes: protocol.neuralRegeneration.transcriptProbes,
          transcriptSeed: seed + 77000 + gen,
        });

        if (isBudgetMatchedRegen) {
          const totalRegenArmCalls = propRes.proposalBudget.oracleCalls + propRes.regenBudget.regenerationCalls;
          const refSerArmCalls = protocol.metaStepsPerGeneration * (1 + protocol.metaSupportTasks * (protocol.innerSteps + 1));
          assert.ok(
            totalRegenArmCalls <= refSerArmCalls,
            `Budget-matched neural_regen (${totalRegenArmCalls}) must not exceed serialization oracle calls (${refSerArmCalls})`,
          );
        }

        genProposals.push({
          arm,
          parentArtifact: current.artifact,
          childArtifact: propRes.childArtifact,
          nextHistoryArtifact: retainsHistory ? propRes.historyArtifact : null,
          proposalBudget: propRes.proposalBudget,
          regenBudget: propRes.regenBudget,
          regenInitialMse: propRes.regenInitialMse,
          regenFinalMse: propRes.regenFinalMse,
          proposalMs: performance.now() - propStart,
        });
      }

      for (const p of genProposals) {
        const useCache = p.arm !== 'serialization_only';
        const parentScore = isolatedScore({
          artifact: p.parentArtifact,
          family,
          holdoutSeed,
          holdoutCount: protocol.holdoutTasksPerGeneration,
          innerSteps: protocol.innerSteps,
          scoreCache: useCache ? scoreCache : null,
        });
        const childScore = isolatedScore({
          artifact: p.childArtifact,
          family,
          holdoutSeed,
          holdoutCount: protocol.holdoutTasksPerGeneration,
          innerSteps: protocol.innerSteps,
          scoreCache: useCache ? scoreCache : null,
        });

        if (p.arm === 'serialization_only') {
          reproductionSummary.serializationOnlyChecks += 1;
          reproductionSummary.serializationOnlyMaxAbsDrift = Math.max(
            reproductionSummary.serializationOnlyMaxAbsDrift,
            Math.abs(childScore.meanLoss - parentScore.meanLoss),
          );
        }

        records.push({
          family,
          seed,
          generation: gen,
          arm: p.arm,
          parentMean: parentScore.meanLoss,
          childMean: childScore.meanLoss,
          proposalOracleCalls: p.proposalBudget.oracleCalls,
          failedAttempts: p.proposalBudget.failedAttempts + p.regenBudget.failedAttempts,
          regenerationCalls: p.proposalBudget.regenerationCalls + p.regenBudget.regenerationCalls,
          regenerationFlops: p.regenBudget.regenerationFlops,
          reconstructionBytes: p.proposalBudget.reconstructionBytes + p.regenBudget.reconstructionBytes,
          regenInitialMse: p.regenInitialMse,
          regenFinalMse: p.regenFinalMse,
          scoreOracleCalls: childScore.budget.oracleCalls,
          proposalMs: p.proposalMs,
        });

        chainStates[p.arm] = {
          artifact: p.childArtifact,
          historyArtifact: p.nextHistoryArtifact,
        };
      }
    }

    // Same-parent AND same-state paired proposer splits at final generation!
    const pairedSupportSeed = seed + 59000;
    const pairedHoldoutSeed = seed + 69000;
    const sharedResetParent = chainStates.evolving_ser_reset.artifact;
    const sharedRetainParent = chainStates.evolving_ser_retain.artifact;
    const sharedRetainHistory = chainStates.evolving_ser_retain.historyArtifact;

    const pairedSpecs = [
      {
        arm: 'paired_evolving_reset',
        targetArtifact: sharedResetParent,
        proposerArtifact: sharedResetParent,
        historyArtifact: null,
        metaObjectiveId: `paired-reset/${family}/${seed}`,
      },
      {
        arm: 'paired_fixed_reset',
        targetArtifact: sharedResetParent,
        proposerArtifact: initialArtifact,
        historyArtifact: null,
        metaObjectiveId: `paired-reset/${family}/${seed}`,
      },
      {
        arm: 'paired_evolving_retain',
        targetArtifact: sharedRetainParent,
        proposerArtifact: sharedRetainParent,
        historyArtifact: sharedRetainHistory,
        metaObjectiveId, // Matches the retained state's objectiveId so BOTH evolving and fixed use the EXACT same retained state!
      },
      {
        arm: 'paired_fixed_retain',
        targetArtifact: sharedRetainParent,
        proposerArtifact: initialArtifact,
        historyArtifact: sharedRetainHistory,
        metaObjectiveId,
      },
    ];

    for (const sp of pairedSpecs) {
      const propRes = isolatedProposeAndReconstruct({
        targetArtifact: sp.targetArtifact,
        proposerArtifact: sp.proposerArtifact,
        historyArtifact: sp.historyArtifact,
        family,
        supportSeed: pairedSupportSeed,
        supportCount: protocol.metaSupportTasks,
        arm: sp.arm,
        innerSteps: protocol.innerSteps,
        metaSteps: protocol.metaStepsPerGeneration,
        metaObjectiveId: sp.metaObjectiveId,
        settings: {},
        transmission: 'serialization',
        regenSteps: 0,
        transcriptProbes: 0,
        transcriptSeed: 0,
      });
      const sc = isolatedScore({
        artifact: propRes.childArtifact,
        family,
        holdoutSeed: pairedHoldoutSeed,
        holdoutCount: protocol.holdoutTasksPerGeneration,
        innerSteps: protocol.innerSteps,
        scoreCache,
      });
      pairedRecords.push({
        family,
        seed,
        arm: sp.arm,
        holdoutMean: sc.meanLoss,
        proposalOracleCalls: propRes.proposalBudget.oracleCalls,
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
  pairedRecords,
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
      regenerationDiagnostics: f.regenerationDiagnostics,
      retainedSer: {
        passes: f.gates.retainedAdaptationSerialization.passes,
        wins: f.gates.retainedAdaptationSerialization.summary.wins,
        medianRel: f.gates.retainedAdaptationSerialization.summary.median,
        signP: f.gates.retainedAdaptationSerialization.summary.oneSidedSignP,
      },
      retainedRegen: {
        passes: f.gates.retainedAdaptationNeuralRegen.passes,
        wins: f.gates.retainedAdaptationNeuralRegen.summary.wins,
        medianRel: f.gates.retainedAdaptationNeuralRegen.summary.median,
        signP: f.gates.retainedAdaptationNeuralRegen.summary.oneSidedSignP,
      },
      retainedRegenBudgetMatched: {
        passes: f.gates.retainedAdaptationNeuralRegenBudgetMatched.passes,
        wins: f.gates.retainedAdaptationNeuralRegenBudgetMatched.summary.wins,
        medianRel: f.gates.retainedAdaptationNeuralRegenBudgetMatched.summary.median,
        signP: f.gates.retainedAdaptationNeuralRegenBudgetMatched.summary.oneSidedSignP,
      },
      proposerChainReset: {
        passes: f.gates.proposerChainReset.passes,
        wins: f.gates.proposerChainReset.summary.wins,
        losses: f.gates.proposerChainReset.summary.losses,
        medianRel: f.gates.proposerChainReset.summary.median,
        signP: f.gates.proposerChainReset.summary.oneSidedSignP,
      },
      proposerChainRetain: {
        passes: f.gates.proposerChainRetain.passes,
        wins: f.gates.proposerChainRetain.summary.wins,
        losses: f.gates.proposerChainRetain.summary.losses,
        medianRel: f.gates.proposerChainRetain.summary.median,
        signP: f.gates.proposerChainRetain.summary.oneSidedSignP,
      },
      pairedSameParentReset: {
        passes: f.gates.pairedSameParentReset.passes,
        wins: f.gates.pairedSameParentReset.summary.wins,
        losses: f.gates.pairedSameParentReset.summary.losses,
        medianRel: f.gates.pairedSameParentReset.summary.median,
        signP: f.gates.pairedSameParentReset.summary.oneSidedSignP,
      },
      pairedSameParentRetain: {
        passes: f.gates.pairedSameParentRetain.passes,
        wins: f.gates.pairedSameParentRetain.summary.wins,
        losses: f.gates.pairedSameParentRetain.summary.losses,
        medianRel: f.gates.pairedSameParentRetain.summary.median,
        signP: f.gates.pairedSameParentRetain.summary.oneSidedSignP,
      },
      conventionalAllPass: f.gates.conventionalAllPass,
      conventionalPassCount: f.gates.conventionalPassCount,
      conventional: Object.fromEntries(
        Object.entries(f.gates.conventional).map(([k, g]) => [k, {
          passes: g.passes,
          wins: g.summary.wins,
          losses: g.summary.losses,
          medianRel: g.summary.median,
          signP: g.summary.oneSidedSignP,
        }]),
      ),
    }]),
  ),
}, null, 2));
