'use strict';

// 2050. Parallel Courses III. Longest prerequisite path in a DAG; O(V+E) time and space. Inputs are preserved.

function solve(n, relations, time) {
  const neighbors = Array.from({ length: n }, () => []);
  const incoming = new Int32Array(n);
  for (const [first, second] of relations) {
    neighbors[first - 1].push(second - 1);
    incoming[second - 1] += 1;
  }
  const finish = time.slice();
  const queue = [];
  for (let node = 0; node < n; node += 1) if (incoming[node] === 0) queue.push(node);
  let answer = 0;
  for (let head = 0; head < queue.length; head += 1) {
    const node = queue[head];
    answer = Math.max(answer, finish[node]);
    for (const target of neighbors[node]) {
      finish[target] = Math.max(finish[target], finish[node] + time[target]);
      incoming[target] -= 1;
      if (incoming[target] === 0) queue.push(target);
    }
  }
  return answer;
}

const minimumTime = solve;
class Solution {
  minimumTime(n, relations, time) { return solve(n, relations, time); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumTime };
