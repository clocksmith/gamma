'use strict';

// 3714. Longest Balanced Substring II.
// O(n) expected time and O(n) space; separately consider one, two, and three distinct letters.
function solve(s) {
  let answer = 0;
  let run = 0;
  let previous = '';
  for (const char of s) {
    run = char === previous ? run + 1 : 1;
    previous = char;
    answer = Math.max(answer, run);
  }
  for (const [first, second] of [['a', 'b'], ['a', 'c'], ['b', 'c']]) {
    let earliest = new Map([[0, -1]]);
    let difference = 0;
    for (let index = 0; index < s.length; index += 1) {
      const char = s[index];
      if (char !== first && char !== second) {
        earliest = new Map([[0, index]]);
        difference = 0;
        continue;
      }
      difference += char === first ? 1 : -1;
      if (earliest.has(difference)) answer = Math.max(answer, index - earliest.get(difference));
      else earliest.set(difference, index);
    }
  }
  const counts = [0, 0, 0];
  const earliest = new Map([['0,0', -1]]);
  for (let index = 0; index < s.length; index += 1) {
    counts[s.charCodeAt(index) - 97] += 1;
    const key = `${counts[0] - counts[1]},${counts[0] - counts[2]}`;
    if (earliest.has(key)) answer = Math.max(answer, index - earliest.get(key));
    else earliest.set(key, index);
  }
  return answer;
}

const longestBalanced = solve;
class Solution {
  longestBalanced(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestBalanced };
