"use strict";
function solve(s) {
const modulus=1000000007,n=s.length,following=new Int32Array(n).fill(n),preceding=new Int32Array(n).fill(-1);let seen=new Map();for(let i=n-1;i>=0;i--){following[i]=seen.has(s[i])?seen.get(s[i]):n;seen.set(s[i],i);}seen=new Map();for(let i=0;i<n;i++){preceding[i]=seen.has(s[i])?seen.get(s[i]):-1;seen.set(s[i],i);}const width=n+1,dp=new Int32Array(width*width),at=(i,j)=>dp[i*width+j];for(let i=n-1;i>=0;i--){dp[i*width+i]=1;for(let j=i+1;j<n;j++){let value;if(s[i]!==s[j])value=at(i+1,j)+at(i,j-1)-at(i+1,j-1);else{const low=following[i],high=preceding[j],inner=at(i+1,j-1);if(low>high)value=2*inner+2;else if(low===high)value=2*inner+1;else value=2*inner-at(low+1,high-1);}dp[i*width+j]=((value%modulus)+modulus)%modulus;}}return dp[n-1];
}
function countPalindromicSubsequences(s) { return solve(s); }
module.exports=solve;
module.exports.countPalindromicSubsequences=countPalindromicSubsequences;
