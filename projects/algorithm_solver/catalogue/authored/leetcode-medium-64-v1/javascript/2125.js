'use strict';

// 2125. Number of Laser Beams in a Bank: multiply device counts in consecutive nonempty rows.
// O(rows * columns) time and O(1) auxiliary space; inputs are read-only.
function solve(bank) {
  let previous = 0;
  let answer = 0;
  for (const row of bank) {
    let devices = 0;
    for (const cell of row) if (cell === '1') devices += 1;
    if (devices > 0) {
      answer += previous * devices;
      previous = devices;
    }
  }
  return answer;
}

const numberOfBeams = solve;
class Solution {
  numberOfBeams(bank) { return solve(bank); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberOfBeams };
