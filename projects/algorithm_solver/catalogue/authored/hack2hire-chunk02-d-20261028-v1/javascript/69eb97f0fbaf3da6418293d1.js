"use strict";
// Hack2Hire 69eb97f0fbaf3da6418293d1 (Implement Simplified Git Diff, level 3) over an INFERRED spec; qualification unknown.

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

function solve(lines1, lines2) {
  const output = [];
  const work = [["segment", 0, lines1.length, 0, lines2.length]];
  while (work.length) {
    const item = work.pop();
    if (item[0] === "emit") { output.push(item[1]); continue; }
    let [, lo1, hi1, lo2, hi2] = item;
    while (lo1 < hi1 && lo2 < hi2 && lines1[lo1] === lines2[lo2]) { output.push("  " + lines1[lo1]); lo1++; lo2++; }
    const suffix = [];
    while (lo1 < hi1 && lo2 < hi2 && lines1[hi1 - 1] === lines2[hi2 - 1]) { hi1--; hi2--; suffix.push("  " + lines1[hi1]); }
    const anchors = chain(uniquePairs(lines1, lo1, hi1, lines2, lo2, hi2));
    const pending = [];
    if (!anchors.length) {
      for (let i = lo1; i < hi1; i++) pending.push(["emit", "- " + lines1[i]]);
      for (let j = lo2; j < hi2; j++) pending.push(["emit", "+ " + lines2[j]]);
    } else {
      let a = lo1, b = lo2;
      for (const [i, j] of anchors) {
        pending.push(["segment", a, i, b, j]);
        pending.push(["emit", "  " + lines1[i]]);
        a = i + 1; b = j + 1;
      }
      pending.push(["segment", a, hi1, b, hi2]);
    }
    for (let s = suffix.length - 1; s >= 0; s--) pending.push(["emit", suffix[s]]);
    for (let p = pending.length - 1; p >= 0; p--) work.push(pending[p]);
  }
  return output;
}

function patienceDiff(lines1, lines2) { return solve(lines1, lines2); }

module.exports = solve;
module.exports.patienceDiff = patienceDiff;
