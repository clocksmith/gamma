import fs from 'node:fs';
import { performance } from 'node:perf_hooks';
import assert from 'node:assert/strict';
import { counter } from './observation.mjs';
import { reconstruct, serialize, sha256 } from './operator.mjs';
import {
  evaluateRule,
  initializeAndCalibrate,
  mean,
  proposeSuccessor,
  sampleTasks,
} from './tasks.mjs';
import { summarizeEffects } from './stats.mjs';

const here = new URL('.', import.meta.url);
const protocol = JSON.parse(fs.readFileSync(new URL('./protocol.selection.json', here), 'utf8'));
const outputPath = process.argv[2];
if (!outputPath) {
  throw new Error('Usage: node projects/self_transform_secant_regen_v1/select.mjs <new-receipt-path>');
}

const sourceFiles = ['observation.mjs', 'autodiff.mjs', 'operator.mjs', 'tasks.mjs', 'stats.mjs', 'select.mjs'];
const sourceHashes = Object.fromEntries(
  sourceFiles.map(name => [name, sha256(fs.readFileSync(new URL(name, here), 'utf8'))]),
);
const protocolHash = sha256(JSON.stringify(protocol));

fs.writeFileSync(
  `${outputPath}.protocol.json`,
  JSON.stringify({ protocol, protocolHash, sourceHashes }, null, 2),
  { flag: 'wx' },
);

const started = performance.now();
const candidateReports = [];
const allRecords = [];
let totalSelectionOracleCalls = 0;

for (const rule of protocol.candidates) {
  const candStart = performance.now();
  for (const family of protocol.families) {
    for (const seed of protocol.selectionSeeds) {
      const prep = initializeAndCalibrate({
        seed,
        family,
        rule,
        config: protocol.preprocessing,
      });
      assert.equal(prep.learnedBudget.oracleCalls, prep.calibrations.sgd.budget.oracleCalls);
      assert.equal(prep.learnedBudget.oracleCalls, prep.calibrations.adam.budget.oracleCalls);
      assert.equal(prep.learnedBudget.oracleCalls, prep.calibrations.bfgs.budget.oracleCalls);
      totalSelectionOracleCalls += prep.sharedChargedOracleCalls;

      const initialArtifact = serialize(prep.initialPhi, rule);
      const states = Object.fromEntries(
        protocol.arms.map(arm => [arm, reconstruct(initialArtifact).phi]),
      );

      for (let gen = 0; gen < protocol.generations; gen += 1) {
        const supportTasks = sampleTasks(family, seed + 51000 + gen * 200, protocol.metaSupportTasks);
        const holdoutTasks = sampleTasks(family, seed + 60000 + gen * 200, protocol.holdoutTasksPerGeneration);

        for (const arm of protocol.arms) {
          const parentPhi = reconstruct(serialize(states[arm], rule)).phi;
          const proposerPhi = arm === 'fixed_ser_reset' ? prep.initialPhi : parentPhi;
          const settings = arm === 'tuned_sgd_reset' ? prep.calibrations.sgd.selected
            : arm === 'tuned_adam_reset' ? prep.calibrations.adam.selected
              : arm === 'tuned_bfgs_reset' ? prep.calibrations.bfgs.selected : {};

          const propBudget = counter();
          const childOut = proposeSuccessor({
            targetPhi: parentPhi,
            proposerPhi,
            rule,
            arm,
            supportTasks,
            innerSteps: protocol.innerSteps,
            metaSteps: protocol.metaStepsPerGeneration,
            metaObjectiveId: `sel/${rule}/${family}/${seed}/g${gen}`,
            initialHistory: null,
            settings,
          }, propBudget);

          const childPhi = reconstruct(serialize(childOut.theta, rule)).phi;
          const scoreBudget = counter();
          const parentLosses = evaluateRule(parentPhi, rule, holdoutTasks, protocol.innerSteps, scoreBudget);
          const childLosses = evaluateRule(childPhi, rule, holdoutTasks, protocol.innerSteps, scoreBudget);
          totalSelectionOracleCalls += propBudget.oracleCalls + scoreBudget.oracleCalls;

          allRecords.push({
            rule,
            family,
            seed,
            generation: gen,
            arm,
            parentMean: mean(parentLosses),
            childMean: mean(childLosses),
            proposalOracleCalls: propBudget.oracleCalls,
            scoreOracleCalls: scoreBudget.oracleCalls,
          });
          states[arm] = childPhi;
        }
      }
    }
  }

  const finalGen = protocol.generations - 1;
  const familyStats = {};
  let minProposerMedian = Infinity;
  let minConvMedian = Infinity;

  for (const family of protocol.families) {
    const evolv = allRecords.filter(r => r.rule === rule && r.family === family && r.generation === finalGen && r.arm === 'evolving_ser_reset');
    const relVs = compArm => summarizeEffects(
      evolv.map(e => {
        const c = allRecords.find(r => r.rule === rule && r.family === family && r.seed === e.seed && r.generation === finalGen && r.arm === compArm);
        return (c.childMean - e.childMean) / c.childMean;
      }),
      protocol.tieTolerance,
    );
    const vsBase = relVs('serialization_only');
    const vsFixed = relVs('fixed_ser_reset');
    const vsSgd = relVs('tuned_sgd_reset');
    const vsAdam = relVs('tuned_adam_reset');
    const vsBfgs = relVs('tuned_bfgs_reset');

    minProposerMedian = Math.min(minProposerMedian, vsFixed.median);
    minConvMedian = Math.min(minConvMedian, vsSgd.median, vsAdam.median, vsBfgs.median);

    familyStats[family] = {
      meanFinalLoss: mean(evolv.map(e => e.childMean)),
      vsSerializationOnly: vsBase,
      vsFixedProposer: vsFixed,
      vsTunedSgd: vsSgd,
      vsTunedAdam: vsAdam,
      vsTunedBfgs: vsBfgs,
    };
  }

  candidateReports.push({
    rule,
    compositeScore: 0.5 * minProposerMedian + 0.5 * minConvMedian,
    minProposerMedian,
    minConvMedian,
    elapsedMs: performance.now() - candStart,
    families: familyStats,
  });
}

const ranked = [...candidateReports].sort((a, b) => (
  (b.compositeScore - a.compositeScore)
  || (b.minProposerMedian - a.minProposerMedian)
  || (protocol.candidates.indexOf(a.rule) - protocol.candidates.indexOf(b.rule))
));

const selectedRule = ranked[0].rule;
const receipt = {
  protocol,
  protocolHash,
  sourceHashes,
  selectedRule,
  totalSelectionOracleCalls,
  ranking: ranked,
  records: allRecords,
  elapsedMs: performance.now() - started,
  node: process.version,
};

fs.writeFileSync(outputPath, JSON.stringify(receipt, null, 2), { flag: 'wx' });
console.log(JSON.stringify({
  selectedRule,
  totalSelectionOracleCalls,
  elapsedMs: receipt.elapsedMs,
  ranking: ranked.map(r => ({
    rule: r.rule,
    compositeScore: r.compositeScore,
    minProposerMedian: r.minProposerMedian,
    minConvMedian: r.minConvMedian,
    families: Object.fromEntries(
      Object.entries(r.families).map(([f, st]) => [f, {
        meanFinalLoss: st.meanFinalLoss,
        medianVsBase: st.vsSerializationOnly.median,
        medianVsFixed: st.vsFixedProposer.median,
        medianVsSgd: st.vsTunedSgd.median,
        medianVsAdam: st.vsTunedAdam.median,
        medianVsBfgs: st.vsTunedBfgs.median,
      }]),
    ),
  })),
}, null, 2));
