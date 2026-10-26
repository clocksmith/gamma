'use strict';

// 1734. Decode XORed Permutation: recover the first value from odd-indexed pairs then decode adjacent XORs.
// O(n) time and O(n) output space with O(1) auxiliary space; inputs are read-only.
function solve(encoded) {
  let first = 0;
  for (let value = 1; value <= encoded.length + 1; value += 1) first ^= value;
  for (let index = 1; index < encoded.length; index += 2) first ^= encoded[index];
  const answer = [first];
  for (const value of encoded) answer.push(answer[answer.length - 1] ^ value);
  return answer;
}

const decode = solve;
class Solution {
  decode(encoded) { return solve(encoded); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, decode };
