"use strict";
// Hack2Hire 69eb97bffbaf3da6418293cf (Implement Simplified Git Diff, level 2) over an INFERRED spec; qualification unknown.

function uniquePairs(lines1, lo1, hi1, lines2, lo2, hi2) {
  const count1 = new Map(), count2 = new Map(), where = new Map();
  for (let i = lo1; i < hi1; i++) count1.set(lines1[i], (count1.get(lines1[i]) || 0) + 1);
  for (let j = lo2; j < hi2; j++) { count2.set(lines2[j], (count2.get(lines2[j]) || 0) + 1); where.set(lines2[j], j); }
  const pairs = [];
  for (let i = lo1; i < hi1; i++) {
    if (count1.get(lines1[i]) === 1 && count2.get(lines1[i]) === 1) pairs.push([i, where.get(lines1[i])]);
  }
  return pairs;
}

// Longest chain increasing in both indices; lexicographically smallest lines1 indices among longest chains.
function chain(pairs) {
  const k = pairs.length;
  if (!k) return [];
  const length = new Array(k);
  const tails = [];
  for (let index = k - 1; index >= 0; index--) {
    const negated = -pairs[index][1];
    let lo = 0, hi = tails.length;
    while (lo < hi) { const mid = (lo + hi) >> 1; if (tails[mid] < negated) lo = mid + 1; else hi = mid; }
    tails[lo] = negated;
    length[index] = lo + 1;
  }
  const best = tails.length;
  const levels = Array.from({length: best + 1}, () => []);
  for (let index = 0; index < k; index++) levels[length[index]].push(index);
  const chosen = [];
  let lastIndex = -1, lastJ = -1;
  for (let need = best; need >= 1; need--) {
    const group = levels[need];
    let lo = 0, hi = group.length;
    while (lo < hi) { const mid = (lo + hi) >> 1; if (group[mid] <= lastIndex) lo = mid + 1; else hi = mid; }
    while (pairs[group[lo]][1] <= lastJ) lo++;
    lastIndex = group[lo];
    lastJ = pairs[lastIndex][1];
    chosen.push([pairs[lastIndex][0], lastJ]);
  }
  return chosen;
}

function solve(lines1, lines2) { return chain(uniquePairs(lines1, 0, lines1.length, lines2, 0, lines2.length)); }

function uniqueCommonAnchors(lines1, lines2) { return solve(lines1, lines2); }

module.exports = solve;
module.exports.uniqueCommonAnchors = uniqueCommonAnchors;
