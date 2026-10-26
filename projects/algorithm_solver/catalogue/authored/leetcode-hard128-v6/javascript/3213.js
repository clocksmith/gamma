'use strict';

// 3213. Construct String with Minimum Cost.
// Aho-Corasick matches feed a shortest-prefix dynamic program; O(26*S+N+Z) time and O(26*S+N) space, Z matched words. Inputs are preserved.

function solve(target, words, costs) {
  const transitions = [Array(26).fill(-1)];
  const failure = [0], output = [0], depth = [0], price = [Infinity];
  for (let index = 0; index < words.length; index += 1) {
    let node = 0;
    for (const character of words[index]) {
      const letter = character.charCodeAt(0) - 97;
      let child = transitions[node][letter];
      if (child === -1) {
        child = transitions.length;
        transitions[node][letter] = child;
        transitions.push(Array(26).fill(-1));
        failure.push(0); output.push(0); depth.push(depth[node] + 1); price.push(Infinity);
      }
      node = child;
    }
    price[node] = Math.min(price[node], costs[index]);
  }
  const queue = [];
  for (let letter = 0; letter < 26; letter += 1) {
    const child = transitions[0][letter];
    if (child === -1) transitions[0][letter] = 0;
    else queue.push(child);
  }
  for (let head = 0; head < queue.length; head += 1) {
    const node = queue[head], fallback = failure[node];
    output[node] = price[fallback] !== Infinity ? fallback : output[fallback];
    for (let letter = 0; letter < 26; letter += 1) {
      const child = transitions[node][letter];
      if (child === -1) transitions[node][letter] = transitions[fallback][letter];
      else {
        failure[child] = transitions[fallback][letter];
        queue.push(child);
      }
    }
  }
  const best = Array(target.length + 1).fill(Infinity);
  best[0] = 0;
  let node = 0;
  for (let end = 1; end <= target.length; end += 1) {
    node = transitions[node][target.charCodeAt(end - 1) - 97];
    let match = price[node] !== Infinity ? node : output[node];
    while (match !== 0) {
      best[end] = Math.min(best[end], best[end - depth[match]] + price[match]);
      match = output[match];
    }
  }
  return best[target.length] === Infinity ? -1 : best[target.length];
}

const minimumCost = solve;
class Solution {
  minimumCost(target, words, costs) { return solve(target, words, costs); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumCost };
