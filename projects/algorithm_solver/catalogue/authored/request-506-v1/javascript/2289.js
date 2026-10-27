// Original candidate. Contract: https://leetcode.com/problems/steps-to-make-array-non-decreasing/
"use strict";
function solve(nums){const st=[];let ans=0;for(const x of nums){let t=0;while(st.length&&st[st.length-1][0]<=x)t=Math.max(t,st.pop()[1]);t=st.length?t+1:0;ans=Math.max(ans,t);st.push([x,t]);}return ans;}
module.exports = solve;
