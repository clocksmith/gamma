'use strict';

// 672. Bulb Switcher II. Enumerate button parity; the first three bulbs distinguish all reachable patterns.

function solve(n, presses) {
  const size = Math.min(n, 3), states = new Set();
  for (let mask = 0; mask < 16; mask += 1) {
    let used = 0;
    for (let bits = mask; bits > 0; bits &= bits - 1) used += 1;
    if (used > presses || (presses - used) % 2 !== 0) continue;
    let state = 0;
    for (let position = 1; position <= size; position += 1) {
      let toggle = Number((mask & 1) !== 0);
      toggle ^= Number((mask & 2) !== 0 && position % 2 === 0);
      toggle ^= Number((mask & 4) !== 0 && position % 2 === 1);
      toggle ^= Number((mask & 8) !== 0 && position % 3 === 1);
      if (!toggle) state |= 1 << (position - 1);
    }
    states.add(state);
  }
  return states.size;
}

const flipLights = solve;
class Solution {
  flipLights(n, presses) { return solve(n, presses); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, flipLights };
