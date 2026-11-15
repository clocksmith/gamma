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
  const { protocol, records, pairedProposerRecords, reproductionSummary } = receipt;
  const finalGen = protocol.generations - 1;
  const tol = protocol.tieTolerance;
  const alpha = protocol.signTestAlpha;

  const byFamily = {};
  for (const family of protocol.families) {
    const famFinal = arm => records.filter(r => r.family === family && r.generation === finalGen && r.arm === arm);
    const heredReset = famFinal('hereditary_reset');
    if (heredReset.length !== protocol.seeds.length) {
      throw new Error(`Expected ${protocol.seeds.length} confirmation replicates for ${family}`);
    }

    const contrastAgainst = (comparatorArm, minMedian) => {
      const pairs = heredReset.map(h => {
        const comp = records.find(r => r.family === family && r.seed === h.seed && r.generation === finalGen && r.arm === comparatorArm);
        if (!comp || !(comp.childMean > 0)) throw new Error(`Missing comparator ${comparatorArm} for seed ${h.seed}`);
        return {
          seed: h.seed,
          hereditaryMean: h.childMean,
          comparatorMean: comp.childMean,
          absoluteReduction: comp.childMean - h.childMean,
          relativeReduction: (comp.childMean - h.childMean) / comp.childMean,
        };
      });
      const summary = summarizeEffects(pairs.map(p => p.relativeReduction), tol);
      return {
        comparator: comparatorArm,
        minimumMedianRequired: minMedian,
        alphaRequired: alpha,
        passes: summary.median >= minMedian && summary.oneSidedSignP < alpha,
        summary,
        pairs,
      };
    };

    // Memory vs rule factorial contrasts
    const factorialMemoryWithinFixed = (() => {
      const fixedRetain = famFinal('fixed_retain');
      const effects = fixedRetain.map(fr => {
        const fxReset = records.find(r => r.family === family && r.seed === fr.seed && r.generation === finalGen && r.arm === 'fixed_reset');
        return (fxReset.childMean - fr.childMean) / fxReset.childMean;
      });
      return summarizeEffects(effects, tol);
    })();

    const factorialMemoryWithinHereditary = (() => {
      const heredRetain = famFinal('hereditary_retain');
      const effects = heredRetain.map(hr => {
        const hReset = records.find(r => r.family === family && r.seed === hr.seed && r.generation === finalGen && r.arm === 'hereditary_reset');
        return (hReset.childMean - hr.childMean) / hReset.childMean;
      });
      return summarizeEffects(effects, tol);
    })();

    const ruleEffectWithRetainedMemory = (() => {
      const heredRetain = famFinal('hereditary_retain');
      const effects = heredRetain.map(hr => {
        const fxRetain = records.find(r => r.family === family && r.seed === hr.seed && r.generation === finalGen && r.arm === 'fixed_retain');
        return (fxRetain.childMean - hr.childMean) / fxRetain.childMean;
      });
      return summarizeEffects(effects, tol);
    })();

    // Same-parent paired proposer split (zero retained memory, identical evolved parent Phi_G)
    const famPairedSelf = pairedProposerRecords.filter(r => r.family === family && r.arm === 'paired_self');
    const pairedContrasts = {};
    for (const pComp of ['paired_fixed', 'paired_parent_unchanged', 'paired_spsa', 'paired_adam', 'paired_bfgs']) {
      const pairs = famPairedSelf.map(ps => {
        const pc = pairedProposerRecords.find(r => r.family === family && r.seed === ps.seed && r.arm === pComp);
        return {
          seed: ps.seed,
          selfMean: ps.holdoutMean,
          comparatorMean: pc.holdoutMean,
          relativeReduction: (pc.holdoutMean - ps.holdoutMean) / pc.holdoutMean,
        };
      });
      const summary = summarizeEffects(pairs.map(p => p.relativeReduction), tol);
      pairedContrasts[pComp] = {
        passesPracticalAndSign: summary.median >= protocol.thresholds.proposerMedianRelative && summary.oneSidedSignP < alpha,
        summary,
        pairs,
      };
    }

    // Subspace alignment progression across generations
    const overlapSummary = {
      initialMean: heredReset.reduce((s, r) => s + r.initialOverlap, 0) / heredReset.length,
      hereditaryFinalMean: heredReset.reduce((s, r) => s + r.childOverlap, 0) / heredReset.length,
      fixedFinalMean: famFinal('fixed_reset').reduce((s, r) => s + r.childOverlap, 0) / heredReset.length,
    };

    // Parent-to-child transition count across all 3 generations
    const allGenHered = records.filter(r => r.family === family && r.arm === 'hereditary_reset');
    const parentChildWins = allGenHered.filter(r => r.childMean < r.parentMean).length;

    const retainedAdaptationGate = contrastAgainst('serialization_only', protocol.thresholds.retainedAdaptationMedianRelative);
    const proposerChainGate = contrastAgainst('fixed_reset', protocol.thresholds.proposerMedianRelative);
    const conventionalGates = {
      tuned_spsa_reset: contrastAgainst('tuned_spsa_reset', protocol.thresholds.conventionalMedianRelative),
      tuned_adam_reset: contrastAgainst('tuned_adam_reset', protocol.thresholds.conventionalMedianRelative),
      tuned_bfgs_reset: contrastAgainst('tuned_bfgs_reset', protocol.thresholds.conventionalMedianRelative),
      tuned_adam_retain: contrastAgainst('tuned_adam_retain', protocol.thresholds.conventionalMedianRelative),
      tuned_bfgs_retain: contrastAgainst('tuned_bfgs_retain', protocol.thresholds.conventionalMedianRelative),
    };

    byFamily[family] = {
      parentToChildTransitions: { wins: parentChildWins, total: allGenHered.length },
      subspaceAlignment: overlapSummary,
      gates: {
        retainedAdaptation: retainedAdaptationGate,
        proposerChainRuleOnly: proposerChainGate,
        pairedSameParentProposer: pairedContrasts.paired_fixed,
        conventionalAllPass: Object.values(conventionalGates).every(g => g.passes),
        conventional: conventionalGates,
      },
      factorialAttribution: {
        memoryEffectWithinFixed: factorialMemoryWithinFixed,
        memoryEffectWithinHereditary: factorialMemoryWithinHereditary,
        ruleEffectWithinRetainedMemory: ruleEffectWithRetainedMemory,
      },
      pairedProposerContrasts: pairedContrasts,
    };
  }

  return {
    selectedRule: protocol.selectedRule,
    reproductionGate: {
      passes: reproductionSummary.allWorkerRoundtripsExact
        && reproductionSummary.allDirectParityAuditsExact
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
