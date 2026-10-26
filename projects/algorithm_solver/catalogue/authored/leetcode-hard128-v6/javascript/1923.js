'use strict';

// 1923. Longest Common Subpath.
// Exact suffix automaton of the shortest path, intersected with every path; O(T + m log m) expected time, O(m) auxiliary space. Inputs are preserved.

function solve(n, paths) {
  let shortest = paths[0];
  for (const path of paths) if (path.length < shortest.length) shortest = path;
  const transitions = [new Map()], lengths = [0], links = [-1];
  let last = 0;
  for (const value of shortest) {
    const current = lengths.length;
    lengths.push(lengths[last] + 1); links.push(0); transitions.push(new Map());
    let previous = last;
    while (previous !== -1 && !transitions[previous].has(value)) {
      transitions[previous].set(value, current); previous = links[previous];
    }
    if (previous !== -1) {
      const target = transitions[previous].get(value);
      if (lengths[previous] + 1 === lengths[target]) links[current] = target;
      else {
        const clone = lengths.length;
        lengths.push(lengths[previous] + 1); links.push(links[target]); transitions.push(new Map(transitions[target]));
        while (previous !== -1 && transitions[previous].get(value) === target) {
          transitions[previous].set(value, clone); previous = links[previous];
        }
        links[target] = links[current] = clone;
      }
    }
    last = current;
  }
  const order = Array.from({ length: lengths.length - 1 }, (_, i) => i + 1).sort((a, b) => lengths[b] - lengths[a]);
  let common = lengths.slice();
  for (const path of paths) {
    const best = Array(lengths.length).fill(0);
    let state = 0, matched = 0;
    for (const value of path) {
      while (state !== 0 && !transitions[state].has(value)) { state = links[state]; matched = Math.min(matched, lengths[state]); }
      if (transitions[state].has(value)) {
        state = transitions[state].get(value); matched += 1; best[state] = Math.max(best[state], matched);
      } else { state = 0; matched = 0; }
    }
    for (const stateIndex of order) {
      const parent = links[stateIndex];
      best[parent] = Math.max(best[parent], Math.min(best[stateIndex], lengths[parent]));
    }
    common = common.map((value, i) => Math.min(value, best[i]));
  }
  return common.reduce((answer, value) => Math.max(answer, value), 0);
}

const longestCommonSubpath = solve;
class Solution {
  longestCommonSubpath(n, paths) { return solve(n, paths); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestCommonSubpath };
