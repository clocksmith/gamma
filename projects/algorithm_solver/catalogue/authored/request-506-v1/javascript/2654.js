// Original implementation. Contract: https://leetcode.com/problems/minimum-number-of-operations-to-make-all-array-elements-equal-to-1/
"use strict";
function solve(a){const gcd=(x,y)=>{while(y){[x,y]=[y,x%y];}return x;};const n=a.length,ones=a.filter(x=>x===1).length;if(ones)return n-ones;let best=n+1;for(let i=0;i<n;i++){let g=0;for(let j=i;j<n;j++){g=gcd(g,a[j]);if(g===1){best=Math.min(best,j-i+1);break;}}}return best===n+1?-1:best+n-2;}
module.exports = solve;
