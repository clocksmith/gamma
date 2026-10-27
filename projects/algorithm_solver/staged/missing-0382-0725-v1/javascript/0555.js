'use strict';

// 555. Split Concatenated Strings. Choose the best orientation outside the cut string and enumerate its orientation and cut.

function solve(strs) {
  const bestParts = strs.map(text => {
    const reversed = text.split('').reverse().join('');
    return text > reversed ? text : reversed;
  });
  let answer = '';
  for (let index = 0; index < strs.length; index += 1) {
    const middle = bestParts.slice(index + 1).concat(bestParts.slice(0, index)).join('');
    for (const text of [strs[index], strs[index].split('').reverse().join('')]) {
      for (let cut = 0; cut < text.length; cut += 1) {
        const candidate = text.slice(cut) + middle + text.slice(0, cut);
        if (candidate > answer) answer = candidate;
      }
    }
  }
  return answer;
}

const splitLoopedString = solve;
class Solution {
  splitLoopedString(strs) { return solve(strs); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, splitLoopedString };
