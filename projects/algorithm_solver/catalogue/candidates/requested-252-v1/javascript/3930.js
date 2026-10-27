'use strict';

// 3930. Power Update After K-th Largest Insertion II.
// Specification: https://leetcode.com/problems/power-update-after-k-th-largest-insertion-ii/description/
// O((n+q) log(n+q) + q log V) time, O(n+q) space; exact modular arithmetic. Inputs are preserved.
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

const powerUpdate = solve;
class Solution {
  powerUpdate(nums, p, queries) { return solve(nums, p, queries); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, powerUpdate };
