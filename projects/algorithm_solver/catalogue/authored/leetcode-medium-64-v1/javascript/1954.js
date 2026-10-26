'use strict';

// 1954. Minimum Garden Perimeter to Collect Enough Apples: binary search the square radius using the exact apple-count polynomial.
// O(log(neededApples + 1)) time and O(1) auxiliary space on the bounded integer domain; inputs are read-only.
function solve(neededApples) {
  const required = BigInt(neededApples);
  function apples(radius) {
    return 2n * radius * (radius + 1n) * (2n * radius + 1n);
  }
  let low = 1n;
  let high = 1n;
  while (apples(high) < required) high *= 2n;
  while (low < high) {
    const middle = (low + high) / 2n;
    if (apples(middle) >= required) high = middle;
    else low = middle + 1n;
  }
  return Number(8n * low);
}

const minimumPerimeter = solve;
class Solution {
  minimumPerimeter(neededApples) { return solve(neededApples); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumPerimeter };
