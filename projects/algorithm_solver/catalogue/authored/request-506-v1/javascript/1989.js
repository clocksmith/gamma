// Original candidate. Contract: https://leetcode.com/problems/maximum-number-of-people-that-can-be-caught-in-tag/
"use strict";
function solve(team,dist){const a=[],b=[];for(let i=0;i<team.length;i++)(team[i]?a:b).push(i);let i=0,j=0,ans=0;while(i<a.length&&j<b.length){if(Math.abs(a[i]-b[j])<=dist){ans++;i++;j++;}else if(a[i]<b[j])i++;else j++;}return ans;}
module.exports = solve;
