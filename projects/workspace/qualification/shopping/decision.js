// Fixed-size paired bootstrap, deterministic resampling. Missing and failed rows
// cannot disappear from the denominator or become fast successful observations.
export function percentile(values, fraction) {
  if (!values.length) return null;
  const sorted = [...values].sort((a, b) => a - b);
  return sorted[Math.max(0, Math.ceil(fraction * sorted.length) - 1)];
}
function ratios(pairs, fraction, contract) {
  let seed = contract.seed >>> 0;
  const random = () => { seed ^= seed << 13; seed ^= seed >>> 17; seed ^= seed << 5; return (seed >>> 0) / 4294967296; };
  const samples = [];
  for (let i = 0; i < contract.acceptance.bootstrapReplicates; i++) {
    const resampled = Array.from({ length: pairs.length }, () => pairs[Math.floor(random() * pairs.length)]);
    samples.push(percentile(resampled.map(pair => pair[0]), fraction) / percentile(resampled.map(pair => pair[1]), fraction));
  }
  return { estimate: percentile(pairs.map(pair => pair[0]), fraction) / percentile(pairs.map(pair => pair[1]), fraction),
    low: percentile(samples, (1 - contract.acceptance.confidence) / 2), high: percentile(samples, 1 - (1 - contract.acceptance.confidence) / 2) };
}
export function shoppingDecision(rows, cases, contract, { sourceUnchanged, smoke }) {
  const byArm = Object.fromEntries(['fawn-dag', 'stock-script'].map(arm => [arm, rows.filter(row => row.arm === arm && !row.learning)]));
  const complete = Object.values(byArm).every(values => values.length === cases.length && new Set(values.map(row => row.caseId)).size === cases.length);
  const validOutcome = row => {
    const trial = cases.find(value => value.id === row.caseId);
    if (!row.learning && (!trial || trial.index !== row.index || trial.fault !== row.fault)) return false;
    if (row.learning || trial.expected === 'completed') return row.completed === true && row.oracle.completed === true;
    return row.completed === false && (row.fault === 'missing-receipt'
      ? row.oracle.submissions === 1 && row.result?.status === 'unknown' : row.oracle.submissions === 0);
  };
  const correctness = complete && rows.every(row => row.passed && validOutcome(row) && !row.error
    && row.oracle.wrongOrders === 0 && row.oracle.duplicateOrders === 0 && row.oracle.submissions <= 1
    && (!row.completed || row.oracle.completed) && row.cleanup.profilesReleased);
  const clean = byArm['fawn-dag'].filter(row => !row.fault);
  const pairs = clean.flatMap(row => {
    const other = byArm['stock-script'].find(value => value.caseId === row.caseId);
    return other && row.completed && other.completed ? [[row.completeMs, other.completeMs]] : [];
  });
  const enough = !smoke && pairs.length === contract.cleanTrials && contract.faults.every(fault =>
    Object.values(byArm).every(values => values.filter(row => row.fault === fault).length === contract.faultTrialsPerKind));
  const groups = new Map();
  for (const row of rows.filter(row => !row.learning && !row.fault)) {
    const key = `${row.arm}:${row.index}`, trace = JSON.stringify({ sku: row.oracle.selectedSku, trace: row.trace });
    if (!groups.has(key)) groups.set(key, new Set());
    groups.get(key).add(trace);
  }
  const repeatable = [...groups.values()].every(values => values.size === 1);
  const eligible = sourceUnchanged && correctness && enough && repeatable;
  const latency = eligible ? { p50Ratio: ratios(pairs, 0.5, contract), p95Ratio: ratios(pairs, 0.95, contract) } : null;
  const summary = Object.fromEntries(Object.entries(byArm).map(([arm, values]) => [arm, {
    attempted: values.length, completed: values.filter(row => row.completed).length,
    correctExpectedBehavior: values.filter(row => row.passed).length,
    cleanP50Ms: percentile(values.filter(row => !row.fault && row.completed).map(row => row.completeMs), 0.5),
    cleanP95Ms: percentile(values.filter(row => !row.fault && row.completed).map(row => row.completeMs), 0.95),
    completeWorkloadMs: rows.filter(row => row.arm === arm).reduce((sum, row) => sum + row.completeMs, 0),
  }]));
  return { complete, sourceUnchanged, correctness, repeatable, enoughSamples: enough, summary, latency,
    scriptLatencyWin: !!latency && latency.p50Ratio.high < contract.acceptance.maxLatencyRatio
      && latency.p95Ratio.high < contract.acceptance.maxLatencyRatio,
    repeatedLocalP95UnderHeadline: eligible && summary['fawn-dag'].cleanP95Ms < contract.acceptance.headlineMs,
    cerebrasComparison: 'unavailable: no original agent or matched live task', cerebrasBeaten: false,
    liveShoppingQualified: false, learningProvider: 'authored field rules; not a model-learning result' };
}
