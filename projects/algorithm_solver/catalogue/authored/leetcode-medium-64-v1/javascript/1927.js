'use strict';

// 1927. Sum Game: compare the fixed digit imbalance with the unmatched question-mark contribution.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(num) {
  const middle = num.length / 2;
  let difference = 0;
  let leftUnknown = 0;
  let rightUnknown = 0;
  for (let index = 0; index < num.length; index += 1) {
    if (num[index] === '?') {
      if (index < middle) leftUnknown += 1;
      else rightUnknown += 1;
    } else {
      const value = num.charCodeAt(index) - 48;
      difference += index < middle ? value : -value;
    }
  }
  if ((leftUnknown + rightUnknown) % 2) return true;
  return 2 * difference !== 9 * (rightUnknown - leftUnknown);
}

const sumGame = solve;
class Solution {
  sumGame(num) { return solve(num); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, sumGame };
