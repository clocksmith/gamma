'use strict';

// 2073. Time Needed to Buy Tickets (Easy).
// Specification: https://leetcode.com/problems/time-needed-to-buy-tickets/description/
// O(n) time, O(1) space; count turns before the kth buyer finishes; preserve tickets.
function solve(tickets, k) {
  const target = tickets[k];
  let seconds = 0;
  for (let index = 0; index < tickets.length; index++) {
    const limit = index <= k ? target : target - 1;
    seconds += Math.min(tickets[index], limit);
  }
  return seconds;
}

const timeRequiredToBuy = solve;
class Solution {
  timeRequiredToBuy(tickets, k) { return solve(tickets, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, timeRequiredToBuy };
