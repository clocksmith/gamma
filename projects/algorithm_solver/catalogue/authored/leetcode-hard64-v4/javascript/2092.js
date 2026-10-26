'use strict';

// 2092. Find All People With Secret. Time-grouped propagation through each simultaneous meeting graph; O(M log M+n) time, O(M+n) space. Inputs are preserved.

function solve(n, meetings, firstPerson) {
  const knows = new Uint8Array(n);
  knows[0] = 1;
  knows[firstPerson] = 1;
  const ordered = meetings.slice().sort((a, b) => a[2] - b[2]);
  let cursor = 0;
  while (cursor < ordered.length) {
    let end = cursor;
    const neighbors = new Map();
    while (end < ordered.length && ordered[end][2] === ordered[cursor][2]) {
      const [first, second] = ordered[end];
      if (!neighbors.has(first)) neighbors.set(first, []);
      if (!neighbors.has(second)) neighbors.set(second, []);
      neighbors.get(first).push(second);
      neighbors.get(second).push(first);
      end += 1;
    }
    const queue = [];
    for (const person of neighbors.keys()) if (knows[person]) queue.push(person);
    const reached = new Set(queue);
    for (let head = 0; head < queue.length; head += 1) {
      const person = queue[head];
      for (const target of neighbors.get(person)) {
        if (!reached.has(target)) {
          reached.add(target);
          knows[target] = 1;
          queue.push(target);
        }
      }
    }
    cursor = end;
  }
  const answer = [];
  for (let person = 0; person < n; person += 1) if (knows[person]) answer.push(person);
  return answer;
}

const findAllPeople = solve;
class Solution {
  findAllPeople(n, meetings, firstPerson) { return solve(n, meetings, firstPerson); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findAllPeople };
