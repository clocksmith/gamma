// Original implementation. Contract: https://leetcode.com/problems/number-of-black-blocks/
"use strict";
function solve(m,n,coordinates){const b=new Map();for(const [x,y] of coordinates)for(const a of [x-1,x])for(const c of [y-1,y])if(a>=0&&a<m-1&&c>=0&&c<n-1){const key=a*n+c;b.set(key,(b.get(key)||0)+1);}const out=[(m-1)*(n-1)-b.size,0,0,0,0];for(const x of b.values())out[x]++;return out;}
module.exports = solve;
