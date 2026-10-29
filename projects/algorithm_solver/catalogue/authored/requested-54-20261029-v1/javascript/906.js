"use strict";
function solve(left,right){const lo=BigInt(left),hi=BigInt(right);let ans=0;
 for(let prefix=1;;prefix++){const s=String(prefix),odd=BigInt(s+s.slice(0,-1).split('').reverse().join('')),even=BigInt(s+s.split('').reverse().join(''));
  if(odd*odd>hi)break;for(const root of [odd,even]){const square=root*root,text=String(square);if(square>=lo&&square<=hi&&text===text.split('').reverse().join(''))ans++;}
 }return ans;
}

function superpalindromesInRange(left, right) { return solve(left, right); }
module.exports=solve;
module.exports.superpalindromesInRange=superpalindromesInRange;
