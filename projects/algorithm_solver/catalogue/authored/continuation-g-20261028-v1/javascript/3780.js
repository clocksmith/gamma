function solve(nums){const best=[[],[],[]];for(const x of nums){const group=best[x%3];group.push(x);group.sort((a,b)=>b-a);if(group.length>3)group.pop();}let answer=0;for(const group of best)if(group.length===3)answer=Math.max(answer,group[0]+group[1]+group[2]);if(best.every(group=>group.length))answer=Math.max(answer,best[0][0]+best[1][0]+best[2][0]);return answer;}

var maximumSum = solve;
module.exports = solve;
