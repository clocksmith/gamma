'use strict';

// 1737. Change Minimum Characters to Satisfy One of Three Conditions: compare shared-letter costs with every strict alphabet boundary.
// O(len(a) + len(b) + 26) time and O(26) auxiliary space; inputs are read-only.
function solve(a, b) {
  const first = new Array(26).fill(0);
  const second = new Array(26).fill(0);
  for (const letter of a) first[letter.charCodeAt(0) - 97] += 1;
  for (const letter of b) second[letter.charCodeAt(0) - 97] += 1;
  let result = a.length + b.length;
  for (let index = 0; index < 26; index += 1) {
    result = Math.min(result, a.length + b.length - first[index] - second[index]);
  }
  let firstPrefix = 0;
  let secondPrefix = 0;
  for (let boundary = 0; boundary < 25; boundary += 1) {
    firstPrefix += first[boundary];
    secondPrefix += second[boundary];
    result = Math.min(result, a.length - firstPrefix + secondPrefix,
                      b.length - secondPrefix + firstPrefix);
  }
  return result;
}

const minCharacters = solve;
class Solution {
  minCharacters(a, b) { return solve(a, b); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minCharacters };
