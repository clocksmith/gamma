"use strict";
function solve(n){let a=[1];while(a.length<n)a=a.map(x=>2*x-1).filter(x=>x<=n).concat(a.map(x=>2*x).filter(x=>x<=n));return a;}

function beautifulArray(n) { return solve(n); }
module.exports=solve;
module.exports.beautifulArray=beautifulArray;
