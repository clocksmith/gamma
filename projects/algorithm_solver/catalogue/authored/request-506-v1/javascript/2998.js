/* Original candidate for LeetCode 2998. Contract: https://leetcode.com/problems/minimum-number-of-operations-to-make-x-and-y-equal/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(x) time and space when x>y, else O(1); bound exceeds direct decrement path budget */
"use strict";
function solve(x,y){if(x<=y)return y-x;const limit=2*x+11,seen=new Uint8Array(limit+1),q=[[x,0]];seen[x]=1;for(let h=0;h<q.length;h++){let [v,d]=q[h];if(v===y)return d;let choices=[v-1,v+1];if(v%5===0)choices.push(v/5);if(v%11===0)choices.push(v/11);for(let w of choices)if(w>=0&&w<=limit&&!seen[w]){seen[w]=1;q.push([w,d+1]);}}}
module.exports = solve;
