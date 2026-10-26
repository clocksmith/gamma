'use strict';

// 599. Minimum Index Sum of Two Lists (Easy).
// Specification: https://leetcode.com/problems/minimum-index-sum-of-two-lists/description/
// O(n + m) expected time, O(n) auxiliary space; return ties in list2 encounter order.
function solve(list1, list2) {
  const positions = new Map(list1.map((name, index) => [name, index]));
  let smallest = Infinity;
  let result = [];
  for (let index = 0; index < list2.length; index++) {
    const name = list2[index];
    if (!positions.has(name)) continue;
    const total = index + positions.get(name);
    if (total < smallest) {
      smallest = total;
      result = [];
    }
    if (total === smallest) result.push(name);
  }
  return result;
}

const findRestaurant = solve;
class Solution {
  findRestaurant(list1, list2) { return solve(list1, list2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findRestaurant };
