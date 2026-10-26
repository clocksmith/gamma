'use strict';

// 1395. Count Number of Teams: count smaller and larger choices around each middle soldier.
// O(n^2) time and O(1) auxiliary space; inputs are read-only.
function solve(rating) {
  let answer = 0;
  for (let middle = 0; middle < rating.length; middle += 1) {
    let leftSmaller = 0;
    let leftLarger = 0;
    let rightSmaller = 0;
    let rightLarger = 0;
    for (let left = 0; left < middle; left += 1) {
      if (rating[left] < rating[middle]) leftSmaller += 1;
      if (rating[left] > rating[middle]) leftLarger += 1;
    }
    for (let right = middle + 1; right < rating.length; right += 1) {
      if (rating[right] < rating[middle]) rightSmaller += 1;
      if (rating[right] > rating[middle]) rightLarger += 1;
    }
    answer += leftSmaller * rightLarger + leftLarger * rightSmaller;
  }
  return answer;
}

const numTeams = solve;
class Solution {
  numTeams(rating) { return solve(rating); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numTeams };
