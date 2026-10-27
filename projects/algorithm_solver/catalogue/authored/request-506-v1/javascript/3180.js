/* Original candidate for LeetCode 3180. Contract: https://leetcode.com/problems/maximum-total-reward-using-operations-i/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n log n + n*M/word_size) time, O(M) bits; M=max reward */
"use strict";
function solve(rewardValues){let bits=1n;for(const x of [...new Set(rewardValues)].sort((a,b)=>a-b)){let shift=BigInt(x);bits|=(bits&((1n<<shift)-1n))<<shift;}return bits.toString(2).length-1;}
module.exports = solve;
