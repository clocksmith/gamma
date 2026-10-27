/* Original candidate for LeetCode 2143. Contract: https://leetcode.com/problems/choose-numbers-from-two-arrays-in-range/
Definition additionally checked against public doocs/leetcode documentation (CC-BY-SA-4.0); original implementation.
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n² V) time, O(n V) space, V=max input value */
"use strict";
function solve(nums1,nums2){const M=1000000007;let dp=new Map(),ans=0;for(let i=0;i<nums1.length;i++){let nd=new Map();for(const [d,v] of [[0,1],...dp])for(const t of [d+nums1[i],d-nums2[i]])nd.set(t,((nd.get(t)||0)+v)%M);dp=nd;ans=(ans+(dp.get(0)||0))%M;}return ans;}
module.exports = solve;
