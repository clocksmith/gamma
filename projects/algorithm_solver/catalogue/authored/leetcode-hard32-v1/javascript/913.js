'use strict';

// 913. Cat and Mouse.
// Retrograde game analysis: O(n * (n + E)) time, O(n^2) space.
function solve(graph) {
  const size = graph.length;
  const outcome = new Uint8Array(2 * size * size);
  const degree = new Int32Array(2 * size * size);
  const state = (mouse, cat, turn) => 2 * (mouse * size + cat) + turn;
  const queue = [];
  for (let mouse = 0; mouse < size; mouse += 1) {
    for (let cat = 1; cat < size; cat += 1) {
      let catMoves = 0;
      for (const node of graph[cat]) if (node !== 0) catMoves += 1;
      for (let turn = 0; turn < 2; turn += 1) {
        const current = state(mouse, cat, turn);
        degree[current] = turn === 0 ? graph[mouse].length : catMoves;
        let winner = mouse === 0 ? 1 : mouse === cat ? 2 : 0;
        if (winner === 0 && degree[current] === 0) winner = 2 - turn;
        if (winner !== 0) {
          outcome[current] = winner;
          queue.push(current);
        }
      }
    }
  }
  for (let head = 0; head < queue.length; head += 1) {
    const current = queue[head];
    const turn = current % 2;
    const pair = Math.floor(current / 2);
    const cat = pair % size;
    const mouse = Math.floor(pair / size);
    const parentTurn = 1 - turn;
    const previousNodes = turn === 0 ? graph[cat] : graph[mouse];
    for (const previous of previousNodes) {
      const parentMouse = turn === 0 ? mouse : previous;
      const parentCat = turn === 0 ? previous : cat;
      if (parentCat === 0) continue;
      const parent = state(parentMouse, parentCat, parentTurn);
      if (outcome[parent] !== 0) continue;
      if (outcome[current] === parentTurn + 1) {
        outcome[parent] = outcome[current];
      } else {
        degree[parent] -= 1;
        if (degree[parent] !== 0) continue;
        outcome[parent] = 2 - parentTurn;
      }
      queue.push(parent);
    }
  }
  return outcome[state(1, 2, 0)];
}

const catMouseGame = solve;
class Solution {
  catMouseGame(graph) { return solve(graph); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, catMouseGame };
