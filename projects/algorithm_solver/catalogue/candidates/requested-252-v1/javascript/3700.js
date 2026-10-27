/**
 * 3700. Number of ZigZag Arrays II
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/number-of-zigzag-arrays-ii/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3700-3799/3700.Number%20of%20ZigZag%20Arrays%20II/README_EN.md
 * Complexity: O((r-l+1)^3 log n) time; O((r-l+1)^2) space.
 * Uses reflection to reduce the transition to m states. Split integer multiplication preserves exact modular arithmetic in JavaScript.
 */

function multiplyMod(a, b, modulus = 1000000007) {
  const low = a % 32768, high = Math.floor(a / 32768);
  return (low * b + ((high * b) % modulus) * 32768) % modulus;
}

function solve(n, l, r) {
  const modulus = 1000000007, width = r - l + 1;
  let matrix = Array.from({ length: width }, (_, row) => Array.from({ length: width }, (_, column) => column >= width - row ? 1 : 0));
  let vector = Array(width).fill(1), exponent = n - 1;
  function square(current) {
    const result = Array.from({ length: width }, () => Array(width).fill(0));
    for (let row = 0; row < width; row += 1) {
      for (let middle = 0; middle < width; middle += 1) {
        if (current[row][middle] === 0) continue;
        for (let column = 0; column < width; column += 1) {
          result[row][column] = (result[row][column] + multiplyMod(current[row][middle], current[middle][column])) % modulus;
        }
      }
    }
    return result;
  }
  while (exponent > 0) {
    if (exponent % 2 === 1) {
      vector = matrix.map(row => row.reduce((sum, value, column) => (sum + multiplyMod(value, vector[column])) % modulus, 0));
    }
    exponent = Math.floor(exponent / 2);
    if (exponent > 0) matrix = square(matrix);
  }
  return 2 * vector.reduce((sum, value) => (sum + value) % modulus, 0) % modulus;
}

function zigZagArrays(n, l, r) {
  return solve(n, l, r);
}

class Solution {
  zigZagArrays(n, l, r) {
    return solve(n, l, r);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, zigZagArrays, Solution };
}
