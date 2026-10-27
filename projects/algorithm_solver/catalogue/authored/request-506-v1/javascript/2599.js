// Original candidate. Contract: https://leetcode.com/problems/make-the-prefix-sum-non-negative/
"use strict";
function solve(nums){const h=[];function push(x){h.push(x);let i=h.length-1;while(i){let p=(i-1)>>1;if(h[p]<=x)break;h[i]=h[p];i=p;}h[i]=x;}function pop(){const ans=h[0],x=h.pop();if(h.length){let i=0;while(i*2+1<h.length){let c=i*2+1;if(c+1<h.length&&h[c+1]<h[c])c++;if(h[c]>=x)break;h[i]=h[c];i=c;}h[i]=x;}return ans;}let total=0,ans=0;for(const x of nums){total+=x;if(x<0)push(x);while(total<0){total-=pop();ans++;}}return ans;}
module.exports = solve;
