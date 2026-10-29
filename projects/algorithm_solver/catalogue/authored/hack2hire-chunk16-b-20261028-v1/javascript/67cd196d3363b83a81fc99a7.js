"use strict";
// Hack2Hire 67cd196d3363b83a81fc99a7 (Portfolio Value Optimization) over an INFERRED spec; qualification unknown.

// Distinct ratios S/P (P <= 1e4) differ by >= 1e-8, so floor(S * 1e8 / P) orders them exactly and ties only equal ratios.
const SCALE = 1e8;

function solve(securities, funds) {
  const groups = new Map();
  for (const [, p, s, a] of securities) {
    const scaled = s * SCALE;
    const key = (scaled - (scaled % p)) / p;
    const g = groups.get(key);
    if (g === undefined) groups.set(key, [p * a, s * a, p, s]);
    else { g[0] += p * a; g[1] += s * a; }
  }
  const keys = Float64Array.from(groups.keys()).sort();
  let remaining = funds, whole = 0, partialNum = 0n, partialDen = 1n;
  for (let k = keys.length - 1; k >= 0; k--) {
    const [cost, value, p, s] = groups.get(keys[k]);
    if (cost <= remaining) { remaining -= cost; whole += value; }
    else { partialNum = BigInt(remaining) * BigInt(s); partialDen = BigInt(p); break; }
  }
  const cents = BigInt(whole) * 100n + (200n * partialNum + partialDen) / (2n * partialDen);
  return String(cents / 100n) + "." + String(cents % 100n).padStart(2, "0");
}

function maximizePortfolioValue(securities, funds) { return solve(securities, funds); }

module.exports = solve;
module.exports.maximizePortfolioValue = maximizePortfolioValue;
