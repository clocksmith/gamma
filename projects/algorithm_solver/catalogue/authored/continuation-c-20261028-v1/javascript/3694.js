function solve(s,k){const move={U:[0,1],D:[0,-1],L:[-1,0],R:[1,0]};let x=0,y=0;for(let i=0;i<k;i++){x+=move[s[i]][0];y+=move[s[i]][1];}const removed=new Set([x+','+y]);for(let i=k;i<s.length;i++){x+=move[s[i]][0]-move[s[i-k]][0];y+=move[s[i]][1]-move[s[i-k]][1];removed.add(x+','+y);}return removed.size;}

var distinctPoints = solve;
module.exports = solve;
