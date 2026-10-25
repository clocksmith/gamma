'use strict';

// 3130. Find All Possible Stable Binary Arrays II.
// O(zero*one) time and space. One ending-state table and one rolling row are sufficient.
function solve(zero, one, limit) {
  const modulus = 1000000007;
  const endingOne = Array.from({ length: zero + 1 }, () => new Uint32Array(one + 1));
  for (let usedOne = 1; usedOne <= Math.min(one, limit); usedOne += 1) endingOne[0][usedOne] = 1;
  let previousZero = new Uint32Array(one + 1);
  for (let usedZero = 1; usedZero <= zero; usedZero += 1) {
    const currentZero = new Uint32Array(one + 1);
    currentZero[0] = usedZero <= limit ? 1 : 0;
    for (let usedOne = 1; usedOne <= one; usedOne += 1) {
      let excluded = usedZero > limit ? endingOne[usedZero - limit - 1][usedOne] : 0;
      currentZero[usedOne] = (previousZero[usedOne] + endingOne[usedZero - 1][usedOne]
        - excluded + modulus) % modulus;
      excluded = usedOne > limit ? currentZero[usedOne - limit - 1] : 0;
      endingOne[usedZero][usedOne] = (currentZero[usedOne - 1] + endingOne[usedZero][usedOne - 1]
        - excluded + modulus) % modulus;
    }
    previousZero = currentZero;
  }
  return (previousZero[one] + endingOne[zero][one]) % modulus;
}

const numberOfStableArrays = solve;
class Solution {
  numberOfStableArrays(zero, one, limit) { return solve(zero, one, limit); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberOfStableArrays };
