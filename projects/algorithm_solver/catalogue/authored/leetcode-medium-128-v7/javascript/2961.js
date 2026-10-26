'use strict';

// 2961. Double Modular Exponentiation: evaluate the two modular exponentiations without constructing the full powers.
// O(n * (log B + log C)) time and O(n) auxiliary space including the result; inputs are read-only.
function solve(variables, target) {
  function powerMod(base, exponent, modulus) {
    let result = 1 % modulus;
    base %= modulus;
    while (exponent > 0) {
      if (exponent % 2 === 1) result = result * base % modulus;
      base = base * base % modulus;
      exponent = Math.floor(exponent / 2);
    }
    return result;
  }
  const result = [];
  for (let index = 0; index < variables.length; index += 1) {
    const [a, b, c, m] = variables[index];
    if (powerMod(powerMod(a, b, 10), c, m) === target) result.push(index);
  }
  return result;
}

const getGoodIndices = solve;
class Solution {
  getGoodIndices(variables, target) { return solve(variables, target); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, getGoodIndices };
