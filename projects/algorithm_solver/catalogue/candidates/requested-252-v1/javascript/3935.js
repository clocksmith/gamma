/**
 * 3935. Power Update After K-th Largest Insertion I
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/power-update-after-k-th-largest-insertion-i/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3935.Power%20Update%20After%20K-th%20Largest%20Insertion%20I/README_EN.md
 * Complexity: O((n+q) log(n+q)+q log V) time, O(n+q) space.
 * Adapted from previously delivered #3930 candidate, same insertion/rank/power semantics with weaker bounds. Preserves input arrays. Native entry pending.
 */

function solve(nums, p, queries) {
  const values = Array.from(new Set([...nums, ...queries.map(query => query[0])])).sort((a, b) => a - b);
  const rank = new Map(values.map((value, index) => [value, index + 1]));
  const tree = new Int32Array(values.length + 1);
  function insert(value) {
    for (let index = rank.get(value); index < tree.length; index += index & -index) tree[index]++;
  }
  function select(order) {
    let index = 0, step = 1;
    while (step * 2 <= values.length) step *= 2;
    for (; step >= 1; step = Math.floor(step / 2)) {
      const next = index + step;
      if (next < tree.length && tree[next] < order) {
        order -= tree[next];
        index = next;
      }
    }
    return values[index];
  }
  const modulus = 1000000007n;
  function modularPower(base, exponent) {
    let result = 1n;
    while (exponent > 0) {
      if (exponent % 2 === 1) result = result * base % modulus;
      base = base * base % modulus;
      exponent = Math.floor(exponent / 2);
    }
    return result;
  }
  for (const value of nums) insert(value);
  let count = nums.length, power = BigInt(p);
  const answer = [];
  for (const [value, order] of queries) {
    insert(value);
    count++;
    power = modularPower(power, select(count - order + 1));
    answer.push(Number(power));
  }
  return answer;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
