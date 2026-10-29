"use strict";
function solve(s){const single=c=>c==='*'?9:Number(c!=='0');function pair(a,b){if(a==='*'&&b==='*')return 15;if(a==='*')return b<='6'?2:1;if(b==='*')return a==='1'?9:a==='2'?6:0;const v=Number(a+b);return Number(v>=10&&v<=26);}let previous=1,current=single(s[0]);for(let i=1;i<s.length;i++){const next=(single(s[i])*current+pair(s[i-1],s[i])*previous)%1000000007;previous=current;current=next;}return current;}

function numDecodings(s){return solve(s);}
module.exports=solve;
module.exports.numDecodings=numDecodings;
