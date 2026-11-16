import fs from 'node:fs';
import { performance } from 'node:perf_hooks';
import assert from 'node:assert/strict';
import {
  counter,
  reconstruct,
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
import { summarizeEffects } from './stats.mjs';

const here = new URL('.', import.meta.url);
const protocol = JSON.parse(fs.readFileSync(new URL('./protocol.selection.json', here), 'utf8'));
const outputPath = process.argv[2];
if (!outputPath) {
  throw new Error('Usage: node projects/self_transform_subspace_v1/select.mjs <new-local-receipt-path>');
}

const sourceFiles = ['observation.mjs', 'operator.mjs', 'tasks.mjs', 'stats.mjs', 'select.mjs'];
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

for (const rule of protocol.candidates) {
  const candidateStart = performance.now();
  const prepReceipts = [];

  for (const family of protocol.families) {
    for (const seed of protocol.selectionSeeds) {
      const prep = initializeAndCalibrate({
        seed,
        family,
        rule,
        config: protocol.preprocessing,
      });
      assert.equal(prep.learnedBudget.scalarQueries, prep.calibrations.spsa.budget.scalarQueries);
      assert.equal(prep.learnedBudget.scalarQueries, prep.calibrations.adam.budget.scalarQueries);
      assert.equal(prep.learnedBudget.scalarQueries, prep.calibrations.bfgs.budget.scalarQueries);

      prepReceipts.push({
        rule,
        family,
        seed,
        selectedInitCandidate: prep.selectedCandidate,
        initialFitness: prep.initialFitness,
        learnedScalarQueries: prep.learnedBudget.scalarQueries,
        sharedChargedScalarQueries: prep.sharedChargedScalarQueries,
        calibratedSettings: {
          spsa: { rate: prep.calibrations.spsa.selected.rate },
          adam: { rate: prep.calibrations.adam.selected.rate, beta: prep.calibrations.adam.selected.beta },
          bfgs: { rate: prep.calibrations.bfgs.selected.rate },
        },
      });

      const evalEnv = makeEnvironment(seed + 50000);
      const supportTasks = sampleTasks(evalEnv, seed + 51000, protocol.metaSupportTasks, family);
      const initialArtifact = serialize(prep.initialPhi, rule);
      const initialOverlap = subspaceOverlap(prep.initialPhi, rule, evalEnv);

      const states = Object.fromEntries(
        protocol.arms.map(arm => [arm, reconstruct(initialArtifact).phi]),
      );

      for (let gen = 0; gen < protocol.generations; gen += 1) {
        const holdoutTasks = sampleTasks(evalEnv, seed + 60000 + gen * 100, protocol.holdoutTasksPerGeneration, family);

        for (const arm of protocol.arms) {
          const parentPhi = reconstruct(serialize(states[arm], rule)).phi;
          const proposerPhi = arm === 'fixed_reset' ? prep.initialPhi : parentPhi;
          const settings = arm === 'tuned_spsa_reset' ? prep.calibrations.spsa.selected
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
            probeBaseSeed: seed + 70000 + gen * 500,
            innerProbeSeed: seed + 80000 + gen * 500,
            initialHistory: null, // Reset across generations for pure rule comparison
            settings,
          }, propBudget);

          const childArtifact = serialize(childOut.theta, rule);
          const childPhi = reconstruct(childArtifact).phi;
          const scoreBudget = counter();
          const parentLosses = evaluateRule(parentPhi, rule, holdoutTasks, protocol.innerSteps, seed + 90000 + gen * 500, scoreBudget);
          const childLosses = evaluateRule(childPhi, rule, holdoutTasks, protocol.innerSteps, seed + 90000 + gen * 500, scoreBudget);

          allRecords.push({
            rule,
            family,
            seed,
            generation: gen,
            arm,
            parentMean: mean(parentLosses),
            childMean: mean(childLosses),
            initialOverlap,
            childOverlap: subspaceOverlap(childPhi, rule, evalEnv),
            proposalScalarQueries: propBudget.scalarQueries,
            scoreScalarQueries: scoreBudget.scalarQueries,
          });

          states[arm] = childPhi;
        }
      }
    }
  }

  // Summarize candidate on selection criterion
  const finalGen = protocol.generations - 1;
  const familyStats = {};
  let minFamilyProposerMedian = Infinity;
  let minFamilyConventionalMedian = Infinity;

  for (const family of protocol.families) {
    const hered = allRecords.filter(r => r.rule === rule && r.family === family && r.generation === finalGen && r.arm === 'hereditary_reset');
    const relVs = compArm => summarizeEffects(
      hered.map(h => {
        const c = allRecords.find(r => r.rule === rule && r.family === family && r.seed === h.seed && r.generation === finalGen && r.arm === compArm);
        return (c.childMean - h.childMean) / c.childMean;
      }),
      protocol.tieTolerance,
    );

    const vsFixed = relVs('fixed_reset');
    const vsBase = relVs('serialization_only');
    const vsSpsa = relVs('tuned_spsa_reset');
    const vsAdam = relVs('tuned_adam_reset');
    const vsBfgs = relVs('tuned_bfgs_reset');

    minFamilyProposerMedian = Math.min(minFamilyProposerMedian, vsFixed.median);
    minFamilyConventionalMedian = Math.min(
      minFamilyConventionalMedian,
      vsSpsa.median,
      vsAdam.median,
      vsBfgs.median,
    );

    familyStats[family] = {
      meanHereditaryFinalLoss: mean(hered.map(h => h.childMean)),
      meanInitialOverlap: mean(hered.map(h => h.initialOverlap)),
      meanFinalOverlap: mean(hered.map(h => h.childOverlap)),
      vsSerializationOnly: vsBase,
      vsFixedProposer: vsFixed,
      vsTunedSpsa: vsSpsa,
      vsTunedAdam: vsAdam,
      vsTunedBfgs: vsBfgs,
    };
  }

  const compositeScore = 0.5 * minFamilyProposerMedian + 0.5 * minFamilyConventionalMedian;
  candidateReports.push({
    rule,
    compositeScore,
    minFamilyProposerMedian,
    minFamilyConventionalMedian,
    elapsedMs: performance.now() - candidateStart,
    families: familyStats,
    preprocessingCount: prepReceipts.length,
  });
}

const ranked = [...candidateReports].sort((a, b) => (
  (b.compositeScore - a.compositeScore)
  || (b.minFamilyProposerMedian - a.minFamilyProposerMedian)
  || (protocol.candidates.indexOf(a.rule) - protocol.candidates.indexOf(b.rule))
));

const selectedRule = ranked[0].rule;
const selectionReceipt = {
  protocol,
  protocolHash,
  sourceHashes,
  selectedRule,
  ranking: ranked,
  records: allRecords,
  elapsedMs: performance.now() - started,
  node: process.version,
};

fs.writeFileSync(outputPath, JSON.stringify(selectionReceipt, null, 2), { flag: 'wx' });
console.log(JSON.stringify({
  selectedRule,
  elapsedMs: selectionReceipt.elapsedMs,
  ranking: ranked.map(r => ({
    rule: r.rule,
    compositeScore: r.compositeScore,
    minFamilyProposerMedian: r.minFamilyProposerMedian,
    minFamilyConventionalMedian: r.minFamilyConventionalMedian,
    families: Object.fromEntries(
      Object.entries(r.families).map(([f, st]) => [f, {
        meanHereditaryFinalLoss: st.meanHereditaryFinalLoss,
        meanFinalOverlap: st.meanFinalOverlap,
        medianVsBase: st.vsSerializationOnly.median,
        medianVsFixed: st.vsFixedProposer.median,
        medianVsSpsa: st.vsTunedSpsa.median,
        medianVsAdam: st.vsTunedAdam.median,
        medianVsBfgs: st.vsTunedBfgs.median,
      }]),
    ),
  })),
}, null, 2));
