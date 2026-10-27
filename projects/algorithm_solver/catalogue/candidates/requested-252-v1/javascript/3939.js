/**
 * 3939. Count Non Adjacent Subsets in a Rooted Tree
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/count-non-adjacent-subsets-in-a-rooted-tree/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3939.Count%20Non%20Adjacent%20Subsets%20in%20a%20Rooted%20Tree/README_EN.md
 * Complexity: O(n*k^2) time, O(n*k) space.
 * parent[i]<i enables reverse-index postorder. Empty subset subtracted. JS split-limb modular multiplication exact; native name pending.
 */

function multiplyMod(a, b, modulus = 1000000007) {
  const low = a % 32768, high = Math.floor(a / 32768);
  return (low * b + ((high * b) % modulus) * 32768) % modulus;
}

function solve(parent, nums, k) {
  const modulus = 1000000007;
  const n = nums.length;
  const skip = Array.from({ length: n }, () => Array(k).fill(0));
  const take = Array.from({ length: n }, () => Array(k).fill(0));
  for (let node = 0; node < n; node += 1) {
    skip[node][0] = 1;
    take[node][nums[node] % k] = 1;
  }
  for (let child = n - 1; child > 0; child -= 1) {
    const node = parent[child];
    const newSkip = Array(k).fill(0);
    const newTake = Array(k).fill(0);
    for (let first = 0; first < k; first += 1) {
      for (let second = 0; second < k; second += 1) {
        const residue = (first + second) % k;
        const ways = (skip[child][second] + take[child][second]) % modulus;
        newSkip[residue] = (newSkip[residue] + multiplyMod(skip[node][first], ways)) % modulus;
        newTake[residue] = (newTake[residue] + multiplyMod(take[node][first], skip[child][second])) % modulus;
      }
    }
    skip[node] = newSkip;
    take[node] = newTake;
  }
  return (skip[0][0] + take[0][0] - 1 + modulus) % modulus;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
