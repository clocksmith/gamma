'use strict';

// 385. Mini Parser.

class NestedInteger {
  constructor(value) { this.value = value; this.items = value === undefined ? [] : null; }
  isInteger() { return this.items === null; }
  add(elem) {
    if (this.items === null) { this.items = []; this.value = undefined; }
    this.items.push(elem);
  }
  setInteger(value) { this.value = value; this.items = null; }
  getInteger() { return this.items === null ? this.value : null; }
  getList() { return this.items; }
}
function solve(s, nestedIntegerType = NestedInteger) {
  if (s[0] !== '[') return new nestedIntegerType(Number(s));
  const stack = [];
  let start = null, result = null;
  for (let i = 0; i < s.length; i += 1) {
    const char = s[i];
    if (char === '[') stack.push(new nestedIntegerType());
    else if (char === ',' || char === ']') {
      if (start !== null) {
        stack[stack.length - 1].add(new nestedIntegerType(Number(s.slice(start, i))));
        start = null;
      }
      if (char === ']') {
        const node = stack.pop();
        if (stack.length > 0) stack[stack.length - 1].add(node);
        else result = node;
      }
    } else if (start === null) start = i;
  }
  return result;
}
const deserialize = solve;
class Solution { deserialize(s) { return solve(s); } }

if (typeof module !== 'undefined') module.exports = { solve, Solution, deserialize, NestedInteger };
