'use strict';

// 522. Longest Uncommon Subsequence II.

function solve(strs) {
  function subsequence(a, b) {
    let index = 0;
    for (const char of b) if (index < a.length && a[index] === char) index += 1;
    return index === a.length;
  }
  const order = strs.map((_, i) => i).sort((a, b) => strs[b].length - strs[a].length);
  for (const i of order) {
    if (strs.every((text, j) => i === j || !subsequence(strs[i], text))) return strs[i].length;
  }
  return -1;
}

const findLUSlength = solve;
class Solution {
  findLUSlength(strs) { return solve(strs); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findLUSlength };
