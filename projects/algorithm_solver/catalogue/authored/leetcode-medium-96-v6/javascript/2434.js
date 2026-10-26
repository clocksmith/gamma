'use strict';

// 2434. Using a Robot to Print the Lexicographically Smallest String: release stack letters whenever they do not exceed the smallest remaining input letter.
// O(n + 26) time and O(n + 26) auxiliary and result space; inputs are read-only.
function solve(s) {
  const remaining = new Int32Array(26);
  for (const character of s) remaining[character.charCodeAt(0) - 97] += 1;
  let smallest = 0;
  const stack = [];
  const result = [];
  for (const character of s) {
    const letter = character.charCodeAt(0) - 97;
    stack.push(letter);
    remaining[letter] -= 1;
    while (smallest < 26 && remaining[smallest] === 0) smallest += 1;
    while (stack.length && stack[stack.length - 1] <= smallest) {
      result.push(String.fromCharCode(97 + stack.pop()));
    }
  }
  return result.join('');
}

const robotWithString = solve;
class Solution {
  robotWithString(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, robotWithString };
