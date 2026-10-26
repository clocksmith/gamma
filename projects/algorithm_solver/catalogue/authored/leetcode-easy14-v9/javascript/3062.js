'use strict';

// 3062. Winner of the Linked List Game (Easy).
// Specification: https://leetcode.com/problems/winner-of-the-linked-list-game/description/
// O(n) time, O(1) space; compare consecutive pairs in the even-length list without mutation.
function solve(head) {
  let scoreDifference = 0;
  let current = head;
  while (current !== null) {
    const partner = current.next;
    if (current.val > partner.val) scoreDifference++;
    if (current.val < partner.val) scoreDifference--;
    current = partner.next;
  }
  if (scoreDifference > 0) return 'Even';
  if (scoreDifference < 0) return 'Odd';
  return 'Tie';
}

const gameResult = solve;
class Solution {
  gameResult(head) { return solve(head); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, gameResult };
