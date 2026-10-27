/* Original candidate for LeetCode 2557. Contract: https://leetcode.com/problems/maximum-number-of-integers-to-choose-from-a-range-ii/
Definition additionally checked against public doocs/leetcode documentation (CC-BY-SA-4.0); original implementation.
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(b log b + b log n) time, O(b) space; exact BigInt intermediate sums */
"use strict";
function solve(banned,n,maxSum){let bs=[...new Set(banned.filter(x=>x<=n))].sort((a,b)=>a-b);bs.push(n+1);let start=1,count=0,budget=BigInt(maxSum);for(const stop of bs){let len=stop-start,lo=0,hi=len;const cost=m=>BigInt(m)*(2n*BigInt(start)+BigInt(m)-1n)/2n;while(lo<hi){let m=Math.floor((lo+hi+1)/2);if(cost(m)<=budget)lo=m;else hi=m-1;}count+=lo;budget-=cost(lo);if(lo<len)return count;start=stop+1;}return count;}
module.exports = solve;
