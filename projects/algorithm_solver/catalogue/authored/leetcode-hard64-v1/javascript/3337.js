'use strict';

// 3337. Total Characters in String After Transformations II: exponentiate the 26-letter transition matrix.
// O(|s| + 26^3 log(t+1)) time and O(26^2) auxiliary space. Inputs are preserved.
function solve(s, t, nums) {
  const modulus = 1000000007n;
  let matrix = Array.from({ length: 26 }, () => Array(26).fill(0n));
  for (let letter = 0; letter < 26; letter += 1) {
    for (let offset = 1; offset <= nums[letter]; offset += 1) matrix[letter][(letter + offset) % 26] += 1n;
  }
  let counts = Array(26).fill(0n);
  for (let index = 0; index < s.length; index += 1) counts[s.charCodeAt(index) - 97] += 1n;
  function multiply(first, second) {
    const product = Array.from({ length: 26 }, () => Array(26).fill(0n));
    for (let row = 0; row < 26; row += 1) {
      for (let middle = 0; middle < 26; middle += 1) {
        if (first[row][middle] === 0n) continue;
        for (let column = 0; column < 26; column += 1) {
          product[row][column] = (product[row][column] + first[row][middle] * second[middle][column]) % modulus;
        }
      }
    }
    return product;
  }
  let exponent = t;
  while (exponent > 0) {
    if (exponent % 2 === 1) {
      const following = Array(26).fill(0n);
      for (let row = 0; row < 26; row += 1) {
        for (let column = 0; column < 26; column += 1) {
          following[column] = (following[column] + counts[row] * matrix[row][column]) % modulus;
        }
      }
      counts = following;
    }
    exponent = Math.floor(exponent / 2);
    if (exponent > 0) matrix = multiply(matrix, matrix);
  }
  let answer = 0n;
  for (const count of counts) answer = (answer + count) % modulus;
  return Number(answer);
}

const lengthAfterTransformations = solve;
class Solution {
  lengthAfterTransformations(s, t, nums) { return solve(s, t, nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, lengthAfterTransformations };
