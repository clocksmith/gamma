'use strict';

// 3435. Frequencies of Shortest Supersequences.
// Duplicate a minimum vertex subset so the remaining precedence graph is acyclic; O(2^d*d^2) time plus output and O(d^2) working space, d<=16. Inputs are preserved.

function solve(words) {
  const letters = [...new Set(words.join(''))].sort(), size = letters.length;
  const rank = new Map(letters.map((letter, index) => [letter, index])), incoming = new Int32Array(size);
  let forced = 0;
  for (const word of words) {
    const first = rank.get(word[0]), second = rank.get(word[1]);
    incoming[second] |= 1 << first;
    if (first === second) forced |= 1 << first;
  }
  const full = (1 << size) - 1;
  let best = size + 1, answers = [];
  for (let duplicated = 0; duplicated <= full; duplicated += 1) {
    let bits = duplicated, amount = 0;
    while (bits) { bits &= bits - 1; amount += 1; }
    if (amount > best || (duplicated & forced) !== forced) continue;
    let remaining = full ^ duplicated;
    while (remaining) {
      let available = remaining, removed = false;
      while (available) {
        const bit = available & -available, node = 31 - Math.clz32(bit);
        available ^= bit;
        if ((incoming[node] & remaining) === 0) { remaining ^= bit; removed = true; break; }
      }
      if (!removed) break;
    }
    if (remaining) continue;
    if (amount < best) { best = amount; answers = []; }
    const counts = Array(26).fill(0);
    letters.forEach((character, index) => { counts[character.charCodeAt(0) - 97] = 1 + ((duplicated >> index) & 1); });
    answers.push(counts);
  }
  return answers;
}

const supersequences = solve;
class Solution {
  supersequences(words) { return solve(words); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, supersequences };
