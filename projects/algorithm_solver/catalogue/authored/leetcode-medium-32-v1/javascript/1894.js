'use strict';

// 1894. Find the Student that Will Replace the Chalk: skip complete classroom cycles.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(chalk, k) {
  let total = 0;
  for (const amount of chalk) total += amount;
  let remaining = k % total;
  for (let index = 0; index < chalk.length; index += 1) {
    if (remaining < chalk[index]) return index;
    remaining -= chalk[index];
  }
  return -1;
}

const chalkReplacer = solve;
class Solution {
  chalkReplacer(chalk, k) { return solve(chalk, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, chalkReplacer };
