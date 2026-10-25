/**
 * 564. Find the Closest Palindrome (Hard).
 * Fresh candidate authored in this conversation; no repository solution copied.
 * Specification: https://leetcode.com/problems/find-the-closest-palindrome/description/
 * Canonical API: solve(n); native alias: nearestPalindromic(n).
 * Inputs are preserved. Gamma independent qualification is pending.
 */
'use strict';

function solve(n) {
  const length = n.length;
  const value = BigInt(n);
  const halfLength = Math.ceil(length / 2);
  const prefix = BigInt(n.slice(0, halfLength));
  const candidates = new Set([
    10n ** BigInt(length - 1) - 1n,
    10n ** BigInt(length) + 1n
  ]);

  for (const delta of [-1n, 0n, 1n]) {
    const adjusted = prefix + delta;
    if (adjusted < 0n) {
      continue;
    }
    const half = adjusted.toString();
    if (half.length !== halfLength) {
      continue;
    }
    const reflected = length % 2 === 1 ? half.slice(0, -1) : half;
    candidates.add(BigInt(half + reflected.split('').reverse().join('')));
  }

  let nearest = null;
  let nearestDistance = null;
  for (const candidate of candidates) {
    if (candidate === value) {
      continue;
    }
    const distance = candidate > value ? candidate - value : value - candidate;
    if (nearest === null || distance < nearestDistance ||
        (distance === nearestDistance && candidate < nearest)) {
      nearest = candidate;
      nearestDistance = distance;
    }
  }
  return nearest.toString();
}

function nearestPalindromic(n) {
  return solve(n);
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, nearestPalindromic };
}
