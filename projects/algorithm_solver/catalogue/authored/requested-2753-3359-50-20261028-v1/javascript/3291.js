"use strict";

function solve(words, target) {
  const next = [new Int32Array(26).fill(-1)];
  for (let i = 0; i < words.length; i++) {
    const w = words[i];
    let u = 0;
    for (let j = 0; j < w.length; j++) {
      const c = w.charCodeAt(j) - 97;
      if (next[u][c] === -1) {
        next[u][c] = next.length;
        next.push(new Int32Array(26).fill(-1));
      }
      u = next[u][c];
    }
  }
  const n = target.length;
  const maxReach = new Int32Array(n);
  for (let i = 0; i < n; i++) {
    let u = 0;
    let j = i;
    while (j < n) {
      const c = target.charCodeAt(j) - 97;
      if (next[u][c] === -1) break;
      u = next[u][c];
      j++;
    }
    maxReach[i] = j - i;
  }
  let steps = 0, curEnd = 0, farthest = 0;
  for (let i = 0; i < n; i++) {
    if (i > farthest) return -1;
    if (i + maxReach[i] > farthest) farthest = i + maxReach[i];
    if (i === curEnd) {
      steps++;
      curEnd = farthest;
      if (curEnd >= n) return steps;
    }
  }
  return curEnd >= n ? steps : -1;
}

function minValidStrings(words, target) {
  return solve(words, target);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.minValidStrings = minValidStrings;
