"use strict";
function solve(l, r) {
function good(value){const digits=String(value);let increasing=true,decreasing=true;for(let i=1;i<digits.length;i++){increasing&&=digits[i]>digits[i-1];decreasing&&=digits[i]<digits[i-1];}return increasing||decreasing;}const monotone=new Set();function extend(value,previous,increasing){monotone.add(value);for(let digit=increasing?previous+1:0;digit<(increasing?10:previous);digit++)extend(value*10+digit,digit,increasing);}for(let first=1;first<=9;first++){extend(first,first,true);extend(first,first,false);}const extras=[...monotone].filter(value=>!good([...String(value)].reduce((sum,digit)=>sum+Number(digit),0)));function prefix(limit){if(limit<=0)return 0;const digits=String(limit).split('').map(Number),memo=new Map();function count(position,total,tight){if(position===digits.length)return good(total)?1:0;const key=position+','+total+','+(tight?1:0);if(memo.has(key))return memo.get(key);const bound=tight?digits[position]:9;let result=0;for(let digit=0;digit<=bound;digit++)result+=count(position+1,total+digit,tight&&digit===bound);memo.set(key,result);return result;}let answer=count(0,0,true)-1;for(const value of extras)if(value<=limit)answer++;return answer;}return prefix(r)-prefix(l-1);
}
function countFancy(l, r) { return solve(l, r); }
module.exports=solve;
module.exports.countFancy=countFancy;
