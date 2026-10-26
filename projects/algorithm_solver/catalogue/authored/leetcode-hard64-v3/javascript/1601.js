'use strict';

// 1601. Maximum Number of Achievable Transfer Requests: enumerate nontrivial request subsets and check net balances; O((n+q)*2^q) time and O(n+q) space.

function solve(n, requests) {
  const transfers = requests.filter(([first, second]) => first !== second);
  const automatic = requests.length - transfers.length;
  let best = 0;
  for (let mask = 0; mask < (1 << transfers.length); mask += 1) {
    let count = 0;
    for (let bits = mask; bits !== 0; bits &= bits - 1) count += 1;
    if (count <= best) continue;
    const balance = Array(n).fill(0);
    for (let index = 0; index < transfers.length; index += 1) {
      if ((mask & (1 << index)) !== 0) {
        balance[transfers[index][0]] -= 1;
        balance[transfers[index][1]] += 1;
      }
    }
    if (balance.every(value => value === 0)) best = count;
  }
  return automatic + best;
}

const maximumRequests = solve;
class Solution {
  maximumRequests(n, requests) { return solve(n, requests); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumRequests };
