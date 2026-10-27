'use strict';

// 602. Friend Requests II: Who Has the Most Friends. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. request_accepted: requester_id, accepter_id, accept_date. Output: id, num. Each accepted pair contributes one friend to each endpoint; maximum is unique in the stated domain.

function solve(request_accepted) {
  const counts = new Map();
  for (const row of request_accepted) {
    for (const id of [row.requester_id, row.accepter_id]) counts.set(id, (counts.get(id) || 0) + 1);
  }
  let winner = null;
  for (const [id, count] of counts) {
    if (winner === null || count > counts.get(winner) || (count === counts.get(winner) && id < winner)) winner = id;
  }
  return winner === null ? [] : [{id: winner, num: counts.get(winner)}];
}

const mostFriends = solve;
class Solution {
  mostFriends(request_accepted) { return solve(request_accepted); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, mostFriends };
