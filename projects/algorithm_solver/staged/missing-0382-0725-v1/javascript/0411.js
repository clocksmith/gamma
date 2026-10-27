'use strict';

// 411. Minimum Unique Word Abbreviation.

function solve(target, dictionary) {
  const length = target.length, distinct = new Set();
  function bitCount(value) { let count = 0; while (value) { value &= value - 1; count += 1; } return count; }
  for (const word of dictionary) {
    if (word.length !== length) continue;
    let difference = 0;
    for (let index = 0; index < length; index += 1) if (target[index] !== word[index]) difference |= 1 << index;
    if (difference === 0) return '';
    distinct.add(difference);
  }
  if (distinct.size === 0) return String(length);
  const differences = Array.from(distinct).sort((a, b) => bitCount(a) - bitCount(b));
  let bestMask = (1 << length) - 1, bestLength = length;
  const visited = new Set();
  function tokenCount(mask) {
    let count = 0, skipped = false;
    for (let index = 0; index < length; index += 1) {
      if (mask & (1 << index)) { count += 1 + Number(skipped); skipped = false; } else skipped = true;
    }
    return count + Number(skipped);
  }
  function search(mask) {
    if (visited.has(mask)) return;
    visited.add(mask);
    const size = tokenCount(mask);
    if (size >= bestLength) return;
    let uncovered = 0;
    for (const difference of differences) if ((difference & mask) === 0) { uncovered = difference; break; }
    if (uncovered === 0) { bestMask = mask; bestLength = size; return; }
    while (uncovered) { const bit = uncovered & -uncovered; uncovered -= bit; search(mask | bit); }
  }
  search(0);
  const parts = []; let skipped = 0;
  for (let index = 0; index < length; index += 1) {
    if (bestMask & (1 << index)) {
      if (skipped) { parts.push(String(skipped)); skipped = 0; }
      parts.push(target[index]);
    } else skipped += 1;
  }
  if (skipped) parts.push(String(skipped));
  return parts.join('');
}


const minAbbreviation = solve;
class Solution {
  minAbbreviation(target, dictionary) { return solve(target, dictionary); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minAbbreviation };
