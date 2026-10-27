'use strict';

// 597. Friend Requests I: Overall Acceptance Rate. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. friend_request: sender_id, send_to_id, request_date; request_accepted: requester_id, accepter_id, accept_date. Output: accept_rate. Deduplicates each table independently, without intersecting pairs.

function _roundedRatio(numerator, denominator, places) {
  let a = BigInt(numerator);
  let b = BigInt(denominator);
  const sign = (a < 0n) !== (b < 0n) ? -1 : 1;
  if (a < 0n) a = -a;
  if (b < 0n) b = -b;
  const scale = 10n ** BigInt(places);
  const rounded = (2n * a * scale + b) / (2n * b);
  return sign * Number(rounded) / Number(scale);
}

function solve(friend_request, request_accepted) {
  const requests = new Set(friend_request.map(row => JSON.stringify([row.sender_id, row.send_to_id])));
  const accepted = new Set(request_accepted.map(row => JSON.stringify([row.requester_id, row.accepter_id])));
  return [{accept_rate: requests.size ? _roundedRatio(accepted.size, requests.size, 2) : 0}];
}

const acceptanceRate = solve;
class Solution {
  acceptanceRate(friend_request, request_accepted) { return solve(friend_request, request_accepted); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, acceptanceRate };
