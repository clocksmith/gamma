'use strict';

// 3292. Minimum Number of Valid Strings to Form Target II: Aho-Corasick longest valid suffixes and prefix-closed segmentation.
// O(26*S + T) time and O(26*S + T) auxiliary space. Inputs are preserved.
function solve(words, target) {
  const transitions = [new Int32Array(26)];
  const depth = [0];
  const failure = [0];
  for (const word of words) {
    let node = 0;
    for (let index = 0; index < word.length; index += 1) {
      const letter = word.charCodeAt(index) - 97;
      if (transitions[node][letter] === 0) {
        transitions[node][letter] = transitions.length;
        transitions.push(new Int32Array(26));
        depth.push(depth[node] + 1);
        failure.push(0);
      }
      node = transitions[node][letter];
    }
  }
  const queue = Array.from(transitions[0]).filter(child => child !== 0);
  for (let head = 0; head < queue.length; head += 1) {
    const node = queue[head];
    for (let letter = 0; letter < 26; letter += 1) {
      const child = transitions[node][letter];
      if (child !== 0) {
        failure[child] = transitions[failure[node]][letter];
        queue.push(child);
      } else {
        transitions[node][letter] = transitions[failure[node]][letter];
      }
    }
  }
  const best = new Int32Array(target.length + 1);
  let node = 0;
  for (let end = 1; end <= target.length; end += 1) {
    node = transitions[node][target.charCodeAt(end - 1) - 97];
    const length = depth[node];
    if (length === 0) return -1;
    best[end] = best[end - length] + 1;
  }
  return best[target.length];
}

const minValidStrings = solve;
class Solution {
  minValidStrings(words, target) { return solve(words, target); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minValidStrings };
