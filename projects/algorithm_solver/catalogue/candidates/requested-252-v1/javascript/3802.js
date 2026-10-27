/**
 * 3802. Number of Ways to Paint Sheets
 * Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
 * Signature: solve(n, limit).
 * Algorithm: For ordered colors with capped capacities a,b, count max(0,a+b-n+1); aggregate positive pairs with sorted suffix sums and remove self-pairs.
 * Complexity: O(m log m) time; O(m) space.
 * Numeric semantics: JavaScript BigInt and Python int accumulate exact pair counts; return a Number/int residue below 1000000007.
 * Mutation: Does not mutate input arrays, rows, strings, or trees.
 * Interface: Canonical solve(n, limit). Native judge method name was not supplied or verified.
 * Specification: https://leetcode.com/problems/number-of-ways-to-paint-sheets/description/
 * Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3800-3899/3802.Number%20of%20Ways%20to%20Paint%20Sheets/README_EN.md
 * Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
 * New readable implementations; no third-party source bodies copied verbatim.
 * No protected tests or private reference implementations used.
 */

function solve(n, limit) {
  const caps = limit.map(value => Math.min(value, n - 1)).sort((a, b) => a - b);
  const prefix = [0n];
  for (const cap of caps) prefix.push(prefix[prefix.length - 1] + BigInt(cap));
  const modulus = 1000000007n;
  let total = 0n;
  for (const cap of caps) {
    let left = 0;
    let right = caps.length;
    const threshold = n - cap;
    while (left < right) {
      const middle = Math.floor((left + right) / 2);
      if (caps[middle] < threshold) left = middle + 1;
      else right = middle;
    }
    const count = caps.length - left;
    let contribution = prefix[caps.length] - prefix[left] + BigInt(count) * BigInt(cap - n + 1);
    contribution -= BigInt(Math.max(0, 2 * cap - n + 1));
    total = (total + contribution) % modulus;
  }
  return Number(total);
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { solve };
}
