'use strict';

// 3003. Maximize the Number of Partitions After Operations.
function bitCount(mask) {
  let count = 0;
  while (mask !== 0) {
    mask &= mask - 1;
    count += 1;
  }
  return count;
}

// O(26^2*n) time, O(n+26) space. No recursion and no rescanning a changed whole string.
function solve(s, k) {
  if (k === 26) return 1;
  const size = s.length;
  const letters = Int32Array.from(s, char => char.charCodeAt(0) - 97);
  const prefixMasks = new Int32Array(size);
  const prefixClosed = new Int32Array(size);
  let mask = 0;
  let closed = 0;
  for (let index = 0; index < size; index += 1) {
    prefixMasks[index] = mask;
    prefixClosed[index] = closed;
    const extended = mask | (1 << letters[index]);
    if (bitCount(extended) > k) {
      closed += 1;
      mask = 1 << letters[index];
    } else {
      mask = extended;
    }
  }
  const nextStart = new Int32Array(size).fill(size);
  const counts = new Int32Array(26);
  let right = 0;
  let distinct = 0;
  for (let left = 0; left < size; left += 1) {
    while (right < size) {
      const letter = letters[right];
      if (counts[letter] === 0 && distinct === k) break;
      if (counts[letter] === 0) distinct += 1;
      counts[letter] += 1;
      right += 1;
    }
    nextStart[left] = right;
    counts[letters[left]] -= 1;
    if (counts[letters[left]] === 0) distinct -= 1;
  }
  const suffixParts = new Int32Array(size + 1);
  for (let index = size - 1; index >= 0; index -= 1) suffixParts[index] = 1 + suffixParts[nextStart[index]];
  let answer = suffixParts[0];
  const nextPosition = new Int32Array(26).fill(size);
  for (let index = size - 1; index >= 0; index -= 1) {
    const order = Array.from({ length: 26 }, (_, letter) => letter)
      .sort((first, second) => nextPosition[first] - nextPosition[second]);
    mask = prefixMasks[index];
    const count = bitCount(mask);
    for (let replacement = 0; replacement < 26; replacement += 1) {
      if (replacement === letters[index]) continue;
      const bit = 1 << replacement;
      let completed = prefixClosed[index];
      let active;
      let activeCount;
      if ((mask & bit) !== 0) {
        active = mask;
        activeCount = count;
      } else if (count === k) {
        completed += 1;
        active = bit;
        activeCount = 1;
      } else {
        active = mask | bit;
        activeCount = count + 1;
      }
      let needed = k - activeCount + 1;
      let boundary = size;
      for (const letter of order) {
        if (nextPosition[letter] === size) break;
        if ((active & (1 << letter)) === 0) {
          needed -= 1;
          if (needed === 0) {
            boundary = nextPosition[letter];
            break;
          }
        }
      }
      answer = Math.max(answer, completed + 1 + suffixParts[boundary]);
    }
    nextPosition[letters[index]] = index;
  }
  return answer;
}

const maxPartitionsAfterOperations = solve;
class Solution {
  maxPartitionsAfterOperations(s, k) { return solve(s, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxPartitionsAfterOperations };
