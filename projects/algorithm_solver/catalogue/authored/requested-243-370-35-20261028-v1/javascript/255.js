"use strict";

function solve(preorder) {
  const stack = [];
  let low = -Infinity;
  for (let i = 0; i < preorder.length; i++) {
    const x = preorder[i];
    if (x < low) return false;
    while (stack.length > 0 && stack[stack.length - 1] < x) {
      low = stack.pop();
    }
    stack.push(x);
  }
  return true;
}

function verifyPreorder(preorder) {
  return solve(preorder);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.verifyPreorder = verifyPreorder;
