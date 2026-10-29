"use strict";
// Hack2Hire 6a4d607d60d5cca82da2fdb8 (Beam Search Decoding, variant 1 of 2) over an INFERRED spec; qualification unknown.

function solve(scores) {
  return scores.map((row) => {
    let best = 0;
    for (let j = 1; j < row.length; j++) if (row[j] > row[best]) best = j;
    return best;
  });
}

function greedyDecode(scores) { return solve(scores); }

module.exports = solve;
module.exports.greedyDecode = greedyDecode;
