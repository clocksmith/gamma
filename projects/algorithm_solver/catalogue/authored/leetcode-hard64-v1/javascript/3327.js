'use strict';

// 3327. Check if DFS Strings Are Palindromes: iterative postorder intervals and exact Manacher palindrome radii.
// O(n) time and O(n) auxiliary space. Inputs are preserved.
function solve(parent, s) {
  const n = parent.length;
  const children = Array.from({ length: n }, () => []);
  for (let node = 1; node < n; node += 1) children[parent[node]].push(node);
  const left = new Int32Array(n);
  const right = new Int32Array(n);
  const text = [];
  const stack = [[0, false]];
  while (stack.length > 0) {
    const [node, exiting] = stack.pop();
    if (exiting) {
      text.push(s[node]);
      right[node] = text.length;
    } else {
      left[node] = text.length;
      stack.push([node, true]);
      for (let index = children[node].length - 1; index >= 0; index -= 1) {
        stack.push([children[node][index], false]);
      }
    }
  }
  const odd = new Int32Array(n);
  let start = 0;
  let end = -1;
  for (let center = 0; center < n; center += 1) {
    let radius = center > end ? 1 : Math.min(odd[start + end - center], end - center + 1);
    while (center - radius >= 0 && center + radius < n && text[center - radius] === text[center + radius]) radius += 1;
    odd[center] = radius;
    if (center + radius - 1 > end) {
      start = center - radius + 1;
      end = center + radius - 1;
    }
  }
  const even = new Int32Array(n);
  start = 0;
  end = -1;
  for (let center = 0; center < n; center += 1) {
    let radius = center > end ? 0 : Math.min(even[start + end - center + 1], end - center + 1);
    while (center - radius - 1 >= 0 && center + radius < n && text[center - radius - 1] === text[center + radius]) radius += 1;
    even[center] = radius;
    if (center + radius - 1 > end) {
      start = center - radius;
      end = center + radius - 1;
    }
  }
  return Array.from({ length: n }, (_, node) => {
    const length = right[node] - left[node];
    const center = Math.floor((left[node] + right[node]) / 2);
    return length % 2 !== 0 ? odd[center] >= Math.floor(length / 2) + 1 : even[center] >= length / 2;
  });
}

const findAnswer = solve;
class Solution {
  findAnswer(parent, s) { return solve(parent, s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findAnswer };
