"use strict";
function solve(s){const cs=[];for(const c of s)if(!cs.length||cs[cs.length-1]!==c)cs.push(c);const n=cs.length,dp=Array.from({length:n},()=>new Array(n).fill(0));for(let l=n-1;l>=0;l--){dp[l][l]=1;for(let r=l+1;r<n;r++){dp[l][r]=1+dp[l+1][r];for(let m=l+1;m<=r;m++)if(cs[m]===cs[l])dp[l][r]=Math.min(dp[l][r],(m>l+1?dp[l+1][m-1]:0)+dp[m][r]);}}return dp[0][n-1];}

function strangePrinter(s){return solve(s);}
module.exports=solve;
module.exports.strangePrinter=strangePrinter;
