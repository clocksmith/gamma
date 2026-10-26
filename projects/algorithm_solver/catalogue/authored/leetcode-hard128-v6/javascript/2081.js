'use strict';

// 2081. Sum of k-Mirror Numbers.
// Enumerate decimal palindromes in increasing order and check their base-k digits. All results in the declared n<=30 domain fit exact JavaScript integers.

function solve(k, n) {
  let answer = 0, found = 0;
  for (let length = 1; found < n; length += 1) {
    const halfLength = Math.ceil(length / 2);
    for (let half = 10 ** (halfLength - 1); half < 10 ** halfLength; half += 1) {
      const prefix = String(half), reflected = length % 2 ? prefix.slice(0, -1) : prefix;
      const value = Number(prefix + reflected.split('').reverse().join(''));
      let remaining = value;
      const digits = [];
      while (remaining > 0) { digits.push(remaining % k); remaining = Math.floor(remaining / k); }
      let palindrome = true;
      for (let left = 0, right = digits.length - 1; left < right; left += 1, right -= 1) if (digits[left] !== digits[right]) { palindrome = false; break; }
      if (palindrome) { answer += value; found += 1; if (found === n) return answer; }
    }
  }
  return answer;
}

const kMirror = solve;
class Solution {
  kMirror(k, n) { return solve(k, n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, kMirror };
