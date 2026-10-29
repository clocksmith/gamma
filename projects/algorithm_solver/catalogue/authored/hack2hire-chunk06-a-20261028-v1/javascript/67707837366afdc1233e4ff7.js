"use strict";
// Hack2Hire 67707837366afdc1233e4ff7 (Find Special Sequence Pairs) over an INFERRED spec; qualification unknown.

const COMPLEMENT = {A: 'T', T: 'A', C: 'G', G: 'C'};

function solve(sequences) {
  const seen = new Map();
  let pairs = 0;
  for (const s of sequences) {
    let partner = '';
    for (let i = s.length - 1; i >= 0; i--) partner += COMPLEMENT[s[i]];
    pairs += seen.get(partner) || 0;
    seen.set(s, (seen.get(s) || 0) + 1);
  }
  return pairs;
}

function countSpecialPairs(sequences) { return solve(sequences); }

module.exports = solve;
module.exports.countSpecialPairs = countSpecialPairs;
