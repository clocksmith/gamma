'use strict';

// 591. Tag Validator. Parse one enclosing root, matched uppercase tags, and opaque CDATA sections.

function solve(code) {
  if (code.length === 0 || code[0] !== '<') return false;
  const stack = [];
  let i = 0;
  while (i < code.length) {
    if (i > 0 && stack.length === 0) return false;
    if (code.startsWith('<![CDATA[', i)) {
      if (stack.length === 0) return false;
      const end = code.indexOf(']]>', i + 9);
      if (end === -1) return false;
      i = end + 3;
    } else if (code.startsWith('</', i)) {
      const end = code.indexOf('>', i + 2);
      if (end === -1 || stack.length === 0 || stack.pop() !== code.slice(i + 2, end)) return false;
      i = end + 1;
    } else if (code[i] === '<') {
      const end = code.indexOf('>', i + 1);
      if (end === -1) return false;
      const name = code.slice(i + 1, end);
      if (!/^[A-Z]{1,9}$/.test(name)) return false;
      stack.push(name); i = end + 1;
    } else i += 1;
  }
  return stack.length === 0;
}

const isValid = solve;
class Solution {
  isValid(code) { return solve(code); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, isValid };
