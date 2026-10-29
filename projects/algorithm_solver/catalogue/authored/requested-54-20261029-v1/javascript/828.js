"use strict";
function solve(s){const last=new Map();let ans=0;
 for(let i=0;i<s.length;i++){const ch=s[i],[a,b]=last.get(ch)||[-1,-1];ans+=(b-a)*(i-b);last.set(ch,[b,i]);}
 for(const [a,b] of last.values())ans+=(b-a)*(s.length-b);return ans;
}

function uniqueLetterString(s) { return solve(s); }
module.exports=solve;
module.exports.uniqueLetterString=uniqueLetterString;
