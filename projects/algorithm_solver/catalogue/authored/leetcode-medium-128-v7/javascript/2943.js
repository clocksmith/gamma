'use strict';

// 2943. Maximize Area of Square Hole in Grid: find consecutive removable-bar runs on both axes and use the smaller opening.
// O(h log h + v log v) time and O(h + v) auxiliary space; inputs are read-only.
function solve(n, m, hBars, vBars) {
  function opening(bars) {
    const ordered = bars.slice().sort((left, right) => left - right);
    let longest = 0;
    let run = 0;
    let previous;
    for (const bar of ordered) {
      run = previous !== undefined && bar === previous + 1 ? run + 1 : 1;
      longest = Math.max(longest, run);
      previous = bar;
    }
    return longest + 1;
  }
  const side = Math.min(opening(hBars), opening(vBars));
  return side * side;
}

const maximizeSquareHoleArea = solve;
class Solution {
  maximizeSquareHoleArea(n, m, hBars, vBars) { return solve(n, m, hBars, vBars); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximizeSquareHoleArea };
