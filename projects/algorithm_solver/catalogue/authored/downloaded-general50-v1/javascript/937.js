'use strict';

// 937. Reorder Data in Log Files (Medium).
// Specification: https://leetcode.com/problems/reorder-data-in-log-files/description/
function solve(logs) {
  const letter = []; const digit = [];
  for (const log of logs) {
    const space = log.indexOf(' ');
    const rest = log.slice(space + 1);
    if (rest[0] >= '0' && rest[0] <= '9') digit.push(log);
    else letter.push(log);
  }
  letter.sort((a, b) => {
    const aSpace = a.indexOf(' '); const bSpace = b.indexOf(' ');
    const aRest = a.slice(aSpace + 1); const bRest = b.slice(bSpace + 1);
    if (aRest !== bRest) return aRest < bRest ? -1 : 1;
    const aId = a.slice(0, aSpace); const bId = b.slice(0, bSpace);
    return aId < bId ? -1 : aId > bId ? 1 : 0;
  });
  return letter.concat(digit);
}
const reorderLogFiles = solve;
class Solution { reorderLogFiles(logs) { return solve(logs); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, reorderLogFiles };
