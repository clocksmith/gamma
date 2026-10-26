'use strict';

// 3441. Minimum Cost Good Caption.
// Suffix dynamic programming tracks the last letter and run length capped at three, then greedily reconstructs the smallest optimum; O(26*n) time and space. Input is preserved.

function solve(caption) {
  const n = caption.length;
  if (n < 3) return '';
  const infinity = 1000000000, width = 78, cost = new Int32Array((n + 1) * width).fill(infinity);
  for (let letter = 0; letter < 26; letter += 1) cost[n * width + 3 * letter + 2] = 0;
  for (let index = n - 1; index >= 0; index -= 1) {
    const original = caption.charCodeAt(index) - 97, following = (index + 1) * width, current = index * width;
    let first = infinity, second = infinity, firstLetter = -1;
    for (let letter = 0; letter < 26; letter += 1) {
      const value = Math.abs(original - letter) + cost[following + 3 * letter];
      if (value < first) { second = first; first = value; firstLetter = letter; }
      else if (value < second) second = value;
    }
    for (let letter = 0; letter < 26; letter += 1) {
      const difference = Math.abs(original - letter), offset = 3 * letter;
      cost[current + offset] = difference + cost[following + offset + 1];
      cost[current + offset + 1] = difference + cost[following + offset + 2];
      cost[current + offset + 2] = Math.min(difference + cost[following + offset + 2], firstLetter !== letter ? first : second);
    }
  }
  let remaining = infinity;
  for (let letter = 0; letter < 26; letter += 1) remaining = Math.min(remaining, Math.abs(caption.charCodeAt(0) - 97 - letter) + cost[width + 3 * letter]);
  const answer = [];
  let previous = -1, run = 0;
  for (let index = 0; index < n; index += 1) {
    const original = caption.charCodeAt(index) - 97;
    for (let letter = 0; letter < 26; letter += 1) {
      if (previous !== -1 && previous !== letter && run < 3) continue;
      const length = previous === letter ? Math.min(3, run + 1) : 1, difference = Math.abs(original - letter);
      if (difference + cost[(index + 1) * width + 3 * letter + length - 1] === remaining) {
        answer.push(String.fromCharCode(97 + letter)); remaining -= difference; previous = letter; run = length; break;
      }
    }
  }
  return answer.join('');
}

const minCostGoodCaption = solve;
class Solution {
  minCostGoodCaption(caption) { return solve(caption); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minCostGoodCaption };
