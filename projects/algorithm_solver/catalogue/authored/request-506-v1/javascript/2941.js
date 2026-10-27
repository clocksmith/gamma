/* Original candidate for LeetCode 2941. Contract: https://leetcode.com/problems/maximum-gcd-sum-of-a-subarray/
Definition additionally checked against public doocs/leetcode documentation (CC-BY-SA-4.0); original implementation.
Development tests only; not admitted or independently qualified.
Positional nums,k. JS returns Number when safe, otherwise exact BigInt; transport BigInt as decimal integer string, never rounded Number.
Complexity: O(n log V log V) conservative time, O(n+log V) space */
"use strict";

function solve(nums, k) {
  function gcd(a, b) {
    while (b) [a, b] = [b, a % b];
    return a;
  }
  const prefix = [0];
  let states = [];
  let answer = 0n;
  for (let index = 0; index < nums.length; index++) {
    const value = nums[index];
    prefix.push(prefix[prefix.length - 1] + value);
    const next = [];
    // Equal GCD states keep the earliest start: all values are positive.
    for (const [previousGcd, start] of [...states, [value, index]]) {
      const currentGcd = gcd(previousGcd, value);
      if (next.length && next[next.length - 1][0] === currentGcd) continue;
      next.push([currentGcd, start]);
    }
    states = next;
    for (const [currentGcd, start] of states) {
      if (index - start + 1 < k) continue;
      const score = BigInt(prefix[index + 1] - prefix[start]) * BigInt(currentGcd);
      if (score > answer) answer = score;
    }
  }
  return answer <= BigInt(Number.MAX_SAFE_INTEGER) ? Number(answer) : answer;
}

module.exports = solve;
