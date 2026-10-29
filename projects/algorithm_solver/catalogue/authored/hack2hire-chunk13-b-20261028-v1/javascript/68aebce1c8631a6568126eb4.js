"use strict";
// Hack2Hire 68aebce1c8631a6568126eb4 (Same Word of HTML Labels) over an INFERRED spec; qualification unknown.

function nextLeaf(tree, stack) {
  while (stack.length) {
    const [text, children] = tree[stack.pop()];
    if (children.length) { for (let i = children.length - 1; i >= 0; i--) stack.push(children[i]); }
    else return text;
  }
  return null;
}

function solve(tree1, tree2) {
  const stack1 = [0], stack2 = [0];
  let a = nextLeaf(tree1, stack1), b = nextLeaf(tree2, stack2), i = 0, j = 0;
  while (a !== null && b !== null) {
    if (a[i] !== b[j]) return false;
    i++; j++;
    if (i === a.length) { a = nextLeaf(tree1, stack1); i = 0; }
    if (j === b.length) { b = nextLeaf(tree2, stack2); j = 0; }
  }
  return a === null && b === null;
}

function sameWord(tree1, tree2) { return solve(tree1, tree2); }

module.exports = solve;
module.exports.sameWord = sameWord;
