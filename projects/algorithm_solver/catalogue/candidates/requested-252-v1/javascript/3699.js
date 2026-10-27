/**
 * 3699. Number of ZigZag Arrays I
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/number-of-zigzag-arrays-i/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3600-3699/3699.Number%20of%20ZigZag%20Arrays%20I/README_EN.md
 * Complexity: O(n(r-l+1)) time; O(r-l+1) space.
 * Strict alternating comparisons; modulus 1e9+7; n >= 3 as specified.
 */

function solve(n, l, r) {
  const modulus = 1000000007, width = r - l + 1;
  let up = Array(width).fill(1), down = Array(width).fill(1);
  for (let length = 1; length < n; length += 1) {
    const nextUp = Array(width).fill(0), nextDown = Array(width).fill(0);
    let running = 0;
    for (let value = 0; value < width; value += 1) { nextUp[value] = running; running = (running + down[value]) % modulus; }
    running = 0;
    for (let value = width - 1; value >= 0; value -= 1) { nextDown[value] = running; running = (running + up[value]) % modulus; }
    up = nextUp; down = nextDown;
  }
  return up.concat(down).reduce((sum, value) => (sum + value) % modulus, 0);
}

function zigZagArrays(n, l, r) {
  return solve(n, l, r);
}

class Solution {
  zigZagArrays(n, l, r) {
    return solve(n, l, r);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, zigZagArrays, Solution };
}
