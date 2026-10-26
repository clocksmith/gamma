'use strict';

// 2513. Minimize the Maximum of Two Arrays: binary search a bound satisfying both individual capacities and their union.
// O(log(divisor1 + divisor2) + log(uniqueCnt1 + uniqueCnt2)) time and O(1) auxiliary space; inputs are read-only.
function solve(divisor1, divisor2, uniqueCnt1, uniqueCnt2) {
  let left = divisor1;
  let right = divisor2;
  while (right !== 0) [left, right] = [right, left % right];
  const common = (divisor1 / left) * divisor2;
  const total = uniqueCnt1 + uniqueCnt2;
  let low = total;
  let high = 2 * total;
  while (low < high) {
    const middle = Math.floor((low + high) / 2);
    const feasible = middle - Math.floor(middle / divisor1) >= uniqueCnt1
      && middle - Math.floor(middle / divisor2) >= uniqueCnt2
      && middle - Math.floor(middle / common) >= total;
    if (feasible) high = middle;
    else low = middle + 1;
  }
  return low;
}

const minimizeSet = solve;
class Solution {
  minimizeSet(divisor1, divisor2, uniqueCnt1, uniqueCnt2) { return solve(divisor1, divisor2, uniqueCnt1, uniqueCnt2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimizeSet };
