'use strict';

// 1397. Find All Good Strings.
// O(26*n*m) time, O(26*m) space, where m = evil.length. All updates are reduced.
function solve(n, s1, s2, evil) {
  const modulus = 1000000007;
  const size = evil.length;
  const pattern = Array.from(evil, char => char.charCodeAt(0) - 97);
  const prefix = new Int32Array(size);
  for (let index = 1; index < size; index += 1) {
    let matched = prefix[index - 1];
    while (matched > 0 && pattern[index] !== pattern[matched]) matched = prefix[matched - 1];
    if (pattern[index] === pattern[matched]) matched += 1;
    prefix[index] = matched;
  }
  const transitions = Array.from({ length: size }, () => new Int32Array(26));
  for (let matched = 0; matched < size; matched += 1) {
    for (let letter = 0; letter < 26; letter += 1) {
      if (letter === pattern[matched]) transitions[matched][letter] = matched + 1;
      else if (matched > 0) transitions[matched][letter] = transitions[prefix[matched - 1]][letter];
    }
  }
  let ways = Array.from({ length: size }, () => new Float64Array(4));
  ways[0][3] = 1;
  for (let position = 0; position < n; position += 1) {
    const lower = s1.charCodeAt(position) - 97;
    const upper = s2.charCodeAt(position) - 97;
    const following = Array.from({ length: size }, () => new Float64Array(4));
    for (let matched = 0; matched < size; matched += 1) {
      for (let flags = 0; flags < 4; flags += 1) {
        const count = ways[matched][flags];
        if (count === 0) continue;
        const start = flags & 1 ? lower : 0;
        const stop = flags & 2 ? upper : 25;
        for (let letter = start; letter <= stop; letter += 1) {
          const nextMatch = transitions[matched][letter];
          if (nextMatch === size) continue;
          let nextFlags = (flags & 1) && letter === lower ? 1 : 0;
          if ((flags & 2) && letter === upper) nextFlags |= 2;
          following[nextMatch][nextFlags] = (following[nextMatch][nextFlags] + count) % modulus;
        }
      }
    }
    ways = following;
  }
  let answer = 0;
  for (const row of ways) for (const count of row) answer = (answer + count) % modulus;
  return answer;
}

const findGoodStrings = solve;
class Solution {
  findGoodStrings(n, s1, s2, evil) { return solve(n, s1, s2, evil); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findGoodStrings };
