// Original candidate implementation. Contract: https://leetcode.com/problems/minimizing-array-after-replacing-pairs-with-their-product/
"use strict";
function solve(nums,k){if(nums.includes(0))return 1;let groups=0,product=1;for(const v of nums){if(groups===0||product>Math.floor(k/v)){groups++;product=v;}else product*=v;}return groups;}
module.exports = solve;
