"use strict";
// Hack2Hire 6a1cd98b8b879849ebc0fdaf (Find Matching Skeletons) over an INFERRED spec; qualification unknown.

function solve(word, skeletons) {
  const out = [];
  for (const skeleton of skeletons) {
    let hidden = null, ok = true;
    for (let i = 0; i < skeleton.length; i++) {
      const ch = skeleton[i];
      if (ch === "-") {
        if (hidden === null) hidden = word[i];
        else if (word[i] !== hidden) { ok = false; break; }
      } else if (ch !== word[i]) { ok = false; break; }
    }
    if (ok) out.push(skeleton);
  }
  return out;
}

function findMatchingSkeletons(word, skeletons) { return solve(word, skeletons); }

module.exports = solve;
module.exports.findMatchingSkeletons = findMatchingSkeletons;
