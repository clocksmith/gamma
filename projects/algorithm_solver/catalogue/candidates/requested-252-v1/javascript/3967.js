/**
 * 3967. Finish Time of Tasks II
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/finish-time-of-tasks-ii/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3967.Finish%20Time%20of%20Tasks%20II/README_EN.md
 * Complexity: O(n) arbitrary-integer operations and O(n) stored integers; bit complexity depends on potentially exponential finish times.
 * Unlike part I, the consulted statement gives no 2^53 bound. JavaScript solve returns BigInt, Python int; JSON must use decimal-string transport. Iterative rerooting uses two extrema with multiplicity, including tied children. Inputs preserved; native method pending.
 */

function solve(n, edges, baseTime) {
  const graph = Array.from({ length: n }, () => []);
  for (const [left, right] of edges) { graph[left].push(right); graph[right].push(left); }
  const parent = new Int32Array(n).fill(-1);
  const order = [0];
  for (let index = 0; index < order.length; index++) {
    const node = order[index];
    for (const child of graph[node]) {
      if (child === parent[node]) continue;
      parent[child] = node;
      order.push(child);
    }
  }
  const base = baseTime.map(value => BigInt(value));
  const down = base.slice();
  for (let index = n - 1; index >= 0; index--) {
    const node = order[index];
    let low = null;
    let high = null;
    for (const child of graph[node]) {
      if (child === parent[node]) continue;
      if (low === null || down[child] < low) low = down[child];
      if (high === null || down[child] > high) high = down[child];
    }
    if (low !== null) down[node] = high + (high - low) + base[node];
  }
  const up = new Array(n).fill(0n);
  let answer = down[0];
  for (const node of order) {
    const incoming = graph[node].map(neighbor => neighbor === parent[node] ? up[node] : down[neighbor]);
    if (incoming.length === 0) { if (base[node] < answer) answer = base[node]; continue; }
    let low1 = null, low2 = null, high1 = null, high2 = null;
    let lowIndex = -1, highIndex = -1;
    for (let index = 0; index < incoming.length; index++) {
      const value = incoming[index];
      if (low1 === null || value < low1) { low2 = low1; low1 = value; lowIndex = index; }
      else if (low2 === null || value < low2) low2 = value;
      if (high1 === null || value > high1) { high2 = high1; high1 = value; highIndex = index; }
      else if (high2 === null || value > high2) high2 = value;
    }
    const finish = high1 + (high1 - low1) + base[node];
    if (finish < answer) answer = finish;
    for (let index = 0; index < graph[node].length; index++) {
      const child = graph[node][index];
      if (child === parent[node]) continue;
      if (incoming.length === 1) up[child] = base[node];
      else {
        const low = index === lowIndex ? low2 : low1;
        const high = index === highIndex ? high2 : high1;
        up[child] = high + (high - low) + base[node];
      }
    }
  }
  return answer;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
