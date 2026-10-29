"use strict";
// Hack2Hire 678951e8402dc47b67a14951 (Currency Exchange, variant 1) over an INFERRED spec; qualification unknown.
function scaled(rate) { // rate = value / 10**4
  const [whole, fraction = ""] = rate.split(".");
  return BigInt(whole) * 10000n + BigInt((fraction + "0000").slice(0, 4));
}
function solve(rates, fromCurrency, toCurrency) {
  if (fromCurrency === toCurrency) return "1";
  const edges = rates.map(([source, target, rate]) => [source, target, scaled(rate)]);
  const currencies = new Set(edges.flatMap(e => [e[0], e[1]]));
  const best = new Map([[fromCurrency, [1n, 0]]]); // currency -> [numerator, steps]: numerator / 10**(4*steps)
  for (let round = 0; round < currencies.size - 1; round++) {
    let changed = false;
    for (const [source, target, value] of edges) {
      const current = best.get(source);
      if (current === undefined) continue;
      const candidate = [current[0] * value, current[1] + 1], previous = best.get(target);
      if (previous === undefined || candidate[0] * 10n ** BigInt(4 * previous[1]) > previous[0] * 10n ** BigInt(4 * candidate[1])) {
        best.set(target, candidate);
        changed = true;
      }
    }
    if (!changed) break;
  }
  if (!best.has(toCurrency)) return "-1";
  const [numerator, steps] = best.get(toCurrency), scale = 4 * steps;
  const digits = String(numerator).padStart(scale + 1, "0");
  const whole = digits.slice(0, digits.length - scale), fraction = digits.slice(digits.length - scale).replace(/0+$/, "");
  return whole + (fraction ? "." + fraction : "");
}
function bestExchangeRate(rates, fromCurrency, toCurrency) { return solve(rates, fromCurrency, toCurrency); }
module.exports = solve;
module.exports.bestExchangeRate = bestExchangeRate;
