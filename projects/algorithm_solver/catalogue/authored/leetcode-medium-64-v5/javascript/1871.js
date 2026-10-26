'use strict';

// 1871. Jump Game VII: maintain the count of reachable predecessors in the permitted jump window.
// O(n) time and O(n) auxiliary space; inputs are read-only.
function solve(s, minJump, maxJump) {
  const reachable = new Uint8Array(s.length);
  reachable[0] = 1;
  let active = 0;
  for (let index = 1; index < s.length; index += 1) {
    if (index >= minJump) active += reachable[index - minJump];
    if (index > maxJump) active -= reachable[index - maxJump - 1];
    if (s[index] === '0' && active > 0) reachable[index] = 1;
  }
  return reachable[s.length - 1] === 1;
}

const canReach = solve;
class Solution {
  canReach(s, minJump, maxJump) { return solve(s, minJump, maxJump); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, canReach };
