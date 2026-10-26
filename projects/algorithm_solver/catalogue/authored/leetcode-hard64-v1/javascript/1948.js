'use strict';

// 1948. Delete Duplicate Folders in System: bottom-up structural interning followed by simultaneous deletion.
// O(S + N*log N + output size) time and O(S + N + output size) space. Inputs are preserved.
function solve(paths) {
  const children = [new Map()];
  for (const path of paths) {
    let node = 0;
    for (const name of path) {
      if (!children[node].has(name)) {
        children[node].set(name, children.length);
        children.push(new Map());
      }
      node = children[node].get(name);
    }
  }
  const shape = new Int32Array(children.length);
  const interned = new Map();
  const frequency = [0];
  const compareNames = (a, b) => a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0;
  for (let node = children.length - 1; node > 0; node -= 1) {
    if (children[node].size === 0) continue;
    const entries = Array.from(children[node], ([name, child]) => [name, shape[child]]);
    entries.sort(compareNames);
    const signature = JSON.stringify(entries);
    if (!interned.has(signature)) {
      interned.set(signature, frequency.length);
      frequency.push(0);
    }
    shape[node] = interned.get(signature);
    frequency[shape[node]] += 1;
  }
  const answer = [];
  const stack = [[0, []]];
  while (stack.length > 0) {
    const [node, path] = stack.pop();
    if (node !== 0 && shape[node] !== 0 && frequency[shape[node]] > 1) continue;
    if (node !== 0) answer.push(path);
    const entries = Array.from(children[node]).sort(compareNames);
    for (let index = entries.length - 1; index >= 0; index -= 1) {
      const [name, child] = entries[index];
      stack.push([child, path.concat(name)]);
    }
  }
  return answer;
}

const deleteDuplicateFolder = solve;
class Solution {
  deleteDuplicateFolder(paths) { return solve(paths); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, deleteDuplicateFolder };
