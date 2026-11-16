import fs from 'node:fs';
import { pathToFileURL } from 'node:url';

export function signProbability(wins, losses) {
  const n = wins + losses;
  if (n === 0) return 1;
  let sum = 0;
  let coeff = 1;
  for (let k = 0; k <= n; k += 1) {
    if (k >= wins) sum += coeff;
    coeff = (coeff * (n - k)) / (k + 1);
  }
  return sum / (2 ** n);
}

export function summarizeEffects(effects, tieTolerance = 1e-6) {
  if (!Array.isArray(effects) || effects.length === 0 || !effects.every(Number.isFinite)) {
    throw new Error('Expected non-empty finite effects array');
  }
  const sorted = [...effects].sort((a, b) => a - b);
  const n = sorted.length;
  const wins = effects.filter(x => x > tieTolerance).length;
  const losses = effects.filter(x => x < -tieTolerance).length;
  const median = (sorted[Math.floor((n - 1) / 2)] + sorted[Math.floor(n / 2)]) / 2;
  const mean = effects.reduce((a, b) => a + b, 0) / n;
  return {
    n,
    wins,
    losses,
    ties: n - wins - losses,
    median,
    mean,
    min: sorted[0],
    max: sorted[n - 1],
    oneSidedSignP: signProbability(wins, losses),
    medianOrderStatisticInterval: n === 12 ? {
      low: sorted[2],
      high: sorted[9],
      coverage: 1 - (2 * (1 + 12 + 66)) / 4096,
      note: 'Exact 96.14% coverage for population median under independent exchangeable replicates; descriptive only.',
    } : null,
  };
}

export function analyzeConfirmation(receipt) {
  const { protocol, records, pairedRecords, reproductionSummary } = receipt;
  const finalGen = protocol.generations - 1;
  const tol = protocol.tieTolerance;
  const alpha = protocol.signTestAlpha;

  const byFamily = {};
  for (const family of protocol.families) {
    const famFinal = arm => records.filter(r => r.family === family && r.generation === finalGen && r.arm === arm);
    const evolvSerReset = famFinal('evolving_ser_reset');
    if (evolvSerReset.length !== protocol.seeds.length) {
      throw new Error(`Expected ${protocol.seeds.length} confirmation replicates for ${family}`);
    }

    const contrastPair = (focalArm, compArm, minMedian) => {
      const focal = famFinal(focalArm);
      const pairs = focal.map(f => {
        const comp = records.find(r => r.family === family && r.seed === f.seed && r.generation === finalGen && r.arm === compArm);
        if (!comp || !(comp.childMean > 0)) throw new Error(`Missing comparator ${compArm} for seed ${f.seed}`);
        return {
          seed: f.seed,
          focalMean: f.childMean,
          comparatorMean: comp.childMean,
          relativeReduction: (comp.childMean - f.childMean) / comp.childMean,
        };
      });
      const summary = summarizeEffects(pairs.map(p => p.relativeReduction), tol);
      return {
        focal: focalArm,
        comparator: compArm,
        minimumMedianRequired: minMedian,
        alphaRequired: alpha,
        passes: summary.median >= minMedian && summary.oneSidedSignP < alpha,
        summary,
        pairs,
      };
    };

    // Multi-generation retained adaptation for BOTH serialization and neural regeneration
    const retainedSer = contrastPair('evolving_ser_reset', 'serialization_only', protocol.thresholds.retainedAdaptationMedianRelative);
    const retainedRegen = contrastPair('evolving_regen_reset', 'serialization_only', protocol.thresholds.retainedAdaptationMedianRelative);
    const retainedRegenMatched = contrastPair('evolving_regen_budget_matched', 'serialization_only', protocol.thresholds.retainedAdaptationMedianRelative);

    // Proposer improvement with IDENTICAL retained state (both reset and retained!)
    const proposerReset = contrastPair('evolving_ser_reset', 'fixed_ser_reset', protocol.thresholds.proposerMedianRelative);
    const proposerRetain = contrastPair('evolving_ser_retain', 'fixed_ser_retain', protocol.thresholds.proposerMedianRelative);
    const proposerRegenReset = contrastPair('evolving_regen_reset', 'fixed_ser_reset', protocol.thresholds.proposerMedianRelative);

    // Serialization vs Neural Regeneration direct comparison
    const serVsRegenStepMatched = contrastPair('evolving_ser_reset', 'evolving_regen_reset', 0);
    const serVsRegenBudgetMatched = contrastPair('evolving_ser_reset', 'evolving_regen_budget_matched', 0);

    // Memory effects within fixed and evolving
    const memoryWithinFixed = contrastPair('fixed_ser_retain', 'fixed_ser_reset', 0);
    const memoryWithinEvolving = contrastPair('evolving_ser_retain', 'evolving_ser_reset', 0);

    // Same-parent paired proposer split (both state = null AND identical retained state!)
    const pairedContrast = (focalArm, compArm) => {
      const fRows = pairedRecords.filter(r => r.family === family && r.arm === focalArm);
      const pairs = fRows.map(f => {
        const c = pairedRecords.find(r => r.family === family && r.seed === f.seed && r.arm === compArm);
        return {
          seed: f.seed,
          focalMean: f.holdoutMean,
          comparatorMean: c.holdoutMean,
          relativeReduction: (c.holdoutMean - f.holdoutMean) / c.holdoutMean,
        };
      });
      const summary = summarizeEffects(pairs.map(p => p.relativeReduction), tol);
      return {
        passes: summary.median >= protocol.thresholds.proposerMedianRelative && summary.oneSidedSignP < alpha,
        summary,
        pairs,
      };
    };

    const pairedReset = pairedContrast('paired_evolving_reset', 'paired_fixed_reset');
    const pairedRetain = pairedContrast('paired_evolving_retain', 'paired_fixed_retain');

    // Conventional controls (matched state!)
    const conventional = {
      tuned_sgd_reset: contrastPair('evolving_ser_reset', 'tuned_sgd_reset', protocol.thresholds.conventionalMedianRelative),
      tuned_adam_reset: contrastPair('evolving_ser_reset', 'tuned_adam_reset', protocol.thresholds.conventionalMedianRelative),
      tuned_bfgs_reset: contrastPair('evolving_ser_reset', 'tuned_bfgs_reset', protocol.thresholds.conventionalMedianRelative),
      tuned_sgd_retain: contrastPair('evolving_ser_retain', 'tuned_sgd_retain', protocol.thresholds.conventionalMedianRelative),
      tuned_adam_retain: contrastPair('evolving_ser_retain', 'tuned_adam_retain', protocol.thresholds.conventionalMedianRelative),
      tuned_bfgs_retain: contrastPair('evolving_ser_retain', 'tuned_bfgs_retain', protocol.thresholds.conventionalMedianRelative),
    };

    // Parent-to-child transitions across all 4 generations
    const allSer = records.filter(r => r.family === family && r.arm === 'evolving_ser_reset');
    const allRegen = records.filter(r => r.family === family && r.arm === 'evolving_regen_reset');

    byFamily[family] = {
      parentToChildTransitions: {
        serialization: { wins: allSer.filter(r => r.childMean < r.parentMean).length, total: allSer.length },
        neuralRegeneration: { wins: allRegen.filter(r => r.childMean < r.parentMean).length, total: allRegen.length },
      },
      regenerationDiagnostics: {
        meanInitialBehavioralMse: allRegen.reduce((s, r) => s + r.regenInitialMse, 0) / allRegen.length,
        meanFinalBehavioralMse: allRegen.reduce((s, r) => s + r.regenFinalMse, 0) / allRegen.length,
      },
      gates: {
        retainedAdaptationSerialization: retainedSer,
        retainedAdaptationNeuralRegen: retainedRegen,
        retainedAdaptationNeuralRegenBudgetMatched: retainedRegenMatched,
        proposerChainReset: proposerReset,
        proposerChainRetain: proposerRetain,
        proposerChainNeuralRegen: proposerRegenReset,
        pairedSameParentReset: pairedReset,
        pairedSameParentRetain: pairedRetain,
        conventionalAllPass: Object.values(conventional).every(g => g.passes),
        conventionalPassCount: Object.values(conventional).filter(g => g.passes).length,
        conventional,
      },
      serializationVsNeuralRegen: {
        stepMatched: serVsRegenStepMatched,
        budgetMatched: serVsRegenBudgetMatched,
      },
      memoryAttribution: {
        memoryWithinFixed,
        memoryWithinEvolving,
      },
    };
  }

  return {
    selectedRule: protocol.selectedRule,
    reproductionGate: {
      passes: reproductionSummary.allWorkerRoundtripsExact
        && reproductionSummary.allDirectParityAuditsExact
        && reproductionSummary.allRegenerationWeightFree
        && reproductionSummary.serializationOnlyMaxAbsDrift === 0,
      ...reproductionSummary,
    },
    families: byFamily,
  };
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const receipt = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  console.log(JSON.stringify(analyzeConfirmation(receipt), null, 2));
}
