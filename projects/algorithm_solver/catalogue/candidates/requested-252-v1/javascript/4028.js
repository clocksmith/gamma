/**
 * 4028. Minimum Operations to Make a Rotated Palindrome II
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/minimum-operations-to-make-a-rotated-palindrome-ii/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4028.Minimum%20Operations%20to%20Make%20a%20Rotated%20Palindrome%20II/README_EN.md
 * Complexity: 13 exact big-integer squares on O(n log n) bits plus O(n log n) packing work; O(n log n) bits of storage.
 * Circular alphabet distance equals Hamming distance across 13 half-circle cuts. For each cut, mirrored disagreement cost is count(ones)-circular_self_convolution(axis). Carry-free Kronecker packing uses a coefficient base >13n and computes all costs exactly, without FFT rounding or optional dependencies. Runtime depends on built-in big-integer multiplication and is unmeasured.
 */

function solve(s) {
  const letters = Array.from(s, ch => ch.charCodeAt(0) - 97), n = letters.length;
  let width = 1, capacity = 16;
  while (capacity <= 13 * n) { width++; capacity *= 16; }
  const zero = '0'.repeat(width), one = '0'.repeat(width - 1) + '1';
  let convolution = 0n, ones = 0;
  for (let cut = 0; cut < 13; cut++) {
    const chunks = new Array(n);
    for (let i = 0; i < n; i++) {
      const bit = (letters[i] - cut + 26) % 26 < 13;
      chunks[n - 1 - i] = bit ? one : zero;
      if (bit) ones++;
    }
    const word = BigInt('0x' + chunks.join(''));
    convolution += word * word;
  }
  const text = convolution.toString(16).padStart(2 * n * width, '0'), coefficients = new Int32Array(2 * n);
  for (let i = 0; i < 2 * n; i++) {
    const end = text.length - i * width;
    coefficients[i] = parseInt(text.slice(end - width, end), 16);
  }
  let answer = Infinity;
  for (let shift = 0; shift < n; shift++) {
    const axis = (2 * shift + n - 1) % n;
    answer = Math.min(answer, shift + ones - coefficients[axis] - coefficients[axis + n]);
  }
  return answer;
}

function minOperations(s) {
  return solve(s);
}

class Solution {
  minOperations(s) {
    return solve(s);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, minOperations, Solution };
}
