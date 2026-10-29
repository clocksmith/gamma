// Original hack2hire:688fe380b3f942cc1004c02a; inferred public-preview contract; qualification unknown.
"use strict";
function eliminateAdjacentDuplicates(text) {
  let previous = null, run = 0, changes = 0;
  for (const ch of text) { if (ch === previous) run++; else { previous = ch; run = 1; } if (run % 2 === 0) changes++; }
  return changes;
}

const solve = eliminateAdjacentDuplicates;
module.exports = solve;
module.exports.eliminateAdjacentDuplicates = eliminateAdjacentDuplicates;
module.exports.Solution = class { eliminateAdjacentDuplicates(...args) { return eliminateAdjacentDuplicates(...args); } };
