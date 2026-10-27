'use strict';

// 725. Split Linked List in Parts. Cut original next links into k parts; earlier parts receive the extra nodes.

function solve(head, k) {
  let length = 0;
  for (let node = head; node; node = node.next) length += 1;
  const base = Math.floor(length / k), extra = length % k, answer = [];
  let node = head;
  for (let part = 0; part < k; part += 1) {
    const size = base + Number(part < extra);
    answer.push(node);
    let previous = null;
    for (let i = 0; i < size; i += 1) { previous = node; node = node.next; }
    if (previous) previous.next = null;
  }
  return answer;
}

const splitListToParts = solve;
class Solution {
  splitListToParts(head, k) { return solve(head, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, splitListToParts };
