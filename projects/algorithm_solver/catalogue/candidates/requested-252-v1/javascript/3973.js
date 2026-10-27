/**
 * 3973. Distinct Gate Paths to LCA
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/distinct-gate-paths-to-lca/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3973.Distinct%20Gate%20Paths%20to%20LCA/README_EN.md
 * Complexity: O((n+q) log n) time, O(n log n) space.
 * Exactly one gate is used per upward move; no gate at the LCA is consumed. Card 0 is blue, 1 red. Matrix products preserve upward order; exact modular multiplication in JavaScript. Inputs preserved; native method pending.
 */

function multiplyMod(a, b, modulus = 1000000007) {
  const low = a % 32768, high = Math.floor(a / 32768);
  return (low * b + ((high * b) % modulus) * 32768) % modulus;
}

function solve(n, parent, gates, queries) {
  const modulus = 1000000007;
  const children = Array.from({ length: n }, () => []);
  for (let node = 1; node < n; node++) children[parent[node]].push(node);
  const depth = new Int32Array(n);
  const order = [0];
  for (let index = 0; index < order.length; index++) {
    const node = order[index];
    for (const child of children[node]) { depth[child] = depth[node] + 1; order.push(child); }
  }
  const levels = Math.floor(Math.log2(n)) + 1;
  const ancestor = [Int32Array.from(parent, value => Math.max(0, value))];
  const matrices = [new Uint32Array(4 * n)];
  for (let node = 0; node < n; node++) {
    const [red, blue, white] = gates[node];
    matrices[0].set([blue, white, white, red], node * 4);
  }
  matrices[0].set([1, 0, 0, 1], 0);
  for (let level = 1; level < levels; level++) {
    const up = new Int32Array(n);
    const result = new Uint32Array(4 * n);
    const previous = ancestor[level - 1];
    const old = matrices[level - 1];
    for (let node = 0; node < n; node++) {
      const middle = previous[node];
      up[node] = previous[middle];
      const i = node * 4, j = middle * 4;
      for (let row = 0; row < 2; row++) {
        for (let column = 0; column < 2; column++) {
          result[i + row * 2 + column] = (multiplyMod(old[i + row * 2], old[j + column]) + multiplyMod(old[i + row * 2 + 1], old[j + 2 + column])) % modulus;
        }
      }
    }
    ancestor.push(up);
    matrices.push(result);
  }
  function lift(node, vector, level) {
    const matrix = matrices[level], offset = node * 4;
    return [ancestor[level][node], [
      (multiplyMod(vector[0], matrix[offset]) + multiplyMod(vector[1], matrix[offset + 2])) % modulus,
      (multiplyMod(vector[0], matrix[offset + 1]) + multiplyMod(vector[1], matrix[offset + 3])) % modulus,
    ]];
  }
  let answer = 0;
  for (const query of queries) {
    let [left, leftCard, right, rightCard] = query;
    let leftVector = [1 - leftCard, leftCard], rightVector = [1 - rightCard, rightCard];
    if (depth[left] < depth[right]) { [left, right] = [right, left]; [leftVector, rightVector] = [rightVector, leftVector]; }
    const difference = depth[left] - depth[right];
    for (let level = 0; level < levels; level++) {
      if ((difference >>> level) & 1) [left, leftVector] = lift(left, leftVector, level);
    }
    if (left !== right) {
      for (let level = levels - 1; level >= 0; level--) {
        if (ancestor[level][left] !== ancestor[level][right]) {
          [left, leftVector] = lift(left, leftVector, level);
          [right, rightVector] = lift(right, rightVector, level);
        }
      }
      [left, leftVector] = lift(left, leftVector, 0);
      [right, rightVector] = lift(right, rightVector, 0);
    }
    const ways = multiplyMod((leftVector[0] + leftVector[1]) % modulus, (rightVector[0] + rightVector[1]) % modulus);
    answer ^= ways;
  }
  return answer;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
