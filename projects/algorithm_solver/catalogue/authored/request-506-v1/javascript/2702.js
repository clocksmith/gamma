/* Original candidate for LeetCode 2702. Contract: https://leetcode.com/problems/minimum-operations-to-make-numbers-non-positive/
Definition additionally checked against public doocs/leetcode documentation (CC-BY-SA-4.0); original implementation.
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n log(max(nums)/y)) time, O(1) extra space */
"use strict";
function solve(nums,x,y){let max=0;for(const a of nums)max=Math.max(max,a);let lo=0,hi=Math.ceil(max/y);while(lo<hi){let t=Math.floor((lo+hi)/2),need=0;for(const a of nums)need+=Math.ceil(Math.max(0,a-t*y)/(x-y));if(need<=t)hi=t;else lo=t+1;}return lo;}
module.exports = solve;
