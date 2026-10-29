"use strict";

function solve(s1, n1, s2, n2) {
  const chars1 = new Set(s1);
  for (let i = 0; i < s2.length; i++) {
    if (!chars1.has(s2[i])) return 0;
  }
  const m = s2.length;
  const seen = new Map();
  const history = [];
  let j = 0;
  for (let block = 1; block <= n1; block++) {
    for (let i = 0; i < s1.length; i++) {
      if (s1[i] === s2[j % m]) j++;
    }
    const rem = j % m;
    history.push(j);
    if (seen.has(rem)) {
      const prevBlock = seen.get(rem);
      const prevJ = history[prevBlock - 1];
      const cycleBlocks = block - prevBlock;
      const cycleJ = j - prevJ;
      const remaining = n1 - block;
      const fullCycles = Math.floor(remaining / cycleBlocks);
      const tail = remaining % cycleBlocks;
      const totalJ = j + fullCycles * cycleJ + (history[prevBlock - 1 + tail] - prevJ);
      return Math.floor(Math.floor(totalJ / m) / n2);
    }
    seen.set(rem, block);
  }
  return Math.floor(Math.floor(j / m) / n2);
}

function getMaxRepetitions(s1, n1, s2, n2) {
  return solve(s1, n1, s2, n2);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.getMaxRepetitions = getMaxRepetitions;
