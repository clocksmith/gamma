"use strict";
// Hack2Hire 67fbdd34216af53465a721a5 (Lowercase Before Uppercase Count) over an INFERRED spec; qualification unknown.

function solve(s) {
  const lastLower = new Int32Array(26).fill(-1), firstUpper = new Int32Array(26).fill(-1);
  for (let i = 0; i < s.length; i++) {
    const code = s.charCodeAt(i);
    if (code >= 97) lastLower[code - 97] = i;
    else if (firstUpper[code - 65] < 0) firstUpper[code - 65] = i;
  }
  let count = 0;
  for (let c = 0; c < 26; c++) {
    if (lastLower[c] < 0 && firstUpper[c] < 0) continue;
    if (lastLower[c] < 0 || firstUpper[c] < 0 || lastLower[c] < firstUpper[c]) count++;
  }
  return count;
}

function countLowerBeforeUpper(s) { return solve(s); }

module.exports = solve;
module.exports.countLowerBeforeUpper = countLowerBeforeUpper;
