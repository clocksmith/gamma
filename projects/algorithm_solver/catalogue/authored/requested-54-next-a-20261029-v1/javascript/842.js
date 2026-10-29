"use strict";
function solve(num){const n=num.length,limit=2**31;for(let i=1;i<=Math.min(10,n-2);i++){if(i>1&&num[0]==='0')break;const a=Number(num.slice(0,i));if(a>=limit)break;
 for(let j=i+1;j<=Math.min(i+10,n-1);j++){if(j-i>1&&num[i]==='0')break;const b=Number(num.slice(i,j));if(b>=limit)break;const sequence=[a,b];let position=j;
  while(position<n){const value=sequence[sequence.length-2]+sequence[sequence.length-1],text=String(value);if(value>=limit||!num.startsWith(text,position))break;sequence.push(value);position+=text.length;}
  if(position===n&&sequence.length>=3)return sequence;
 }}return [];
}

function splitIntoFibonacci(num) { return solve(num); }
module.exports=solve;
module.exports.splitIntoFibonacci=splitIntoFibonacci;
