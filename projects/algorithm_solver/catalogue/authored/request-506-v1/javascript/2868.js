// Original implementation. Contract: https://leetcode.com/problems/the-wording-game/
"use strict";
function solve(a,b){const words=[...a.map(w=>[w,0]),...b.map(w=>[w,1])].sort((x,y)=>x[0]<y[0]?1:-1),winning=[Array(27).fill(false),Array(27).fill(false)];let answer=false;for(const [word,owner] of words){const c=word.charCodeAt(0)-97,wins=!(winning[1-owner][c]||winning[1-owner][c+1]);winning[owner][c] ||= wins;if(owner===0&&word===a[0])answer=wins;}return answer;}
module.exports = solve;
