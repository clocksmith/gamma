"use strict";
// Hack2Hire 696442bb3b4797da7459a055 (File System Directory Size Sum) over an INFERRED spec; qualification unknown.

function solve(root, limit) {
  let answer = 0;
  const lists = [root.children], next = [0], totals = [0];
  while (lists.length) {
    const top = lists.length - 1, kids = lists[top];
    if (next[top] < kids.length) {
      const child = kids[next[top]++];
      if (child.children !== undefined) { lists.push(child.children); next.push(0); totals.push(0); }
      else totals[top] += child.size;
    } else {
      lists.pop(); next.pop();
      const total = totals.pop();
      if (total <= limit) answer += total;
      if (totals.length) totals[totals.length - 1] += total;
    }
  }
  return answer;
}

function sumDirectorySizes(root, limit) { return solve(root, limit); }

module.exports = solve;
module.exports.sumDirectorySizes = sumDirectorySizes;
