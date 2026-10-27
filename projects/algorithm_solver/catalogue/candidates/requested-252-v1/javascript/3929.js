/**
 * 3929. Minimum Partition Score II
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/minimum-partition-score-ii/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3929.Minimum%20Partition%20Score%20II/README_EN.md
 * Complexity: O(n log(S^2)) arithmetic operations, O(n) space; S=sum(nums).
 * Positive nums<=1000 and n<=50000. Exact BigInt hull comparisons/penalty arithmetic; final <=1.251e15 Number. Lagrangian convex-count optimization; native entry pending. Not benchmarked.
 */

function solve(nums, k) {
  const prefix = [0n];
  for (const value of nums) prefix.push(prefix[prefix.length - 1] + BigInt(value));
  const total = prefix[prefix.length - 1];
  if (k === 1) return Number(total * (total + 1n) / 2n);
  if (k === nums.length) {
    let result = 0n;
    for (const value of nums) result += BigInt(value) * BigInt(value + 1) / 2n;
    return Number(result);
  }
  function penalized(penalty) {
    const hull = [[0n, 0n, 0]];
    let head = 0;
    let cost = 0n;
    let count = 0;
    for (let index = 1; index < prefix.length; index += 1) {
      const value = prefix[index];
      let best = hull[head][0] * value + hull[head][1];
      count = hull[head][2];
      while (head + 1 < hull.length) {
        const following = hull[head + 1][0] * value + hull[head + 1][1];
        if (following > best) break;
        head += 1;
        if (following < best) {
          best = following;
          count = hull[head][2];
        } else count = Math.max(count, hull[head][2]);
      }
      cost = value * value + penalty + best;
      count += 1;
      const line = [-2n * value, cost + value * value, count];
      while (hull.length - head >= 2) {
        const first = hull[hull.length - 2];
        const second = hull[hull.length - 1];
        if ((second[1] - first[1]) * (second[0] - line[0]) > (line[1] - second[1]) * (first[0] - second[0])) hull.pop();
        else break;
      }
      hull.push(line);
    }
    return [cost, count];
  }
  let low = 0n;
  let high = total * total + 1n;
  while (low + 1n < high) {
    const middle = (low + high) / 2n;
    if (penalized(middle)[1] >= k) low = middle;
    else high = middle;
  }
  const [cost] = penalized(low);
  return Number((cost - low * BigInt(k) + total) / 2n);
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
