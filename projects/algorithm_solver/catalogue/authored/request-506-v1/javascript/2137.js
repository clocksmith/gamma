// Original candidate. Contract: https://leetcode.com/problems/pour-water-between-buckets-to-make-water-levels-equal/
"use strict";
function solve(buckets,loss){let lo=Infinity,hi=0;for(const x of buckets){lo=Math.min(lo,x);hi=Math.max(hi,x);}const ratio=1-loss/100;for(let t=0;t<70;t++){const mid=(lo+hi)/2;let net=0;for(const x of buckets)net+=(x-mid)*(x>mid?ratio:1);if(net>=0)lo=mid;else hi=mid;}return lo;}
module.exports = solve;
