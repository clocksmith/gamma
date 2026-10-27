// Original candidate implementation. Contract: https://leetcode.com/problems/minimum-array-end/
"use strict";

function solve(n, x) {
  let remaining = BigInt(n - 1);
  let answer = BigInt(x);
  let bit = 1n;
  const requiredBits = BigInt(x);
  while (remaining) {
    if ((requiredBits & bit) === 0n) {
      if (remaining & 1n) answer |= bit;
      remaining >>= 1n;
    }
    bit <<= 1n;
  }
  // Preserve precision even beyond the declared problem domain.
  if (answer > BigInt(Number.MAX_SAFE_INTEGER)) return answer;
  return Number(answer);
}

module.exports = solve;
