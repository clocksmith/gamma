function solve(capacity){const p=[0];for(const x of capacity)p.push(p[p.length-1]+x);const counts=new Map();let answer=0;for(let r=2;r<capacity.length;r++){const l=r-2,key=capacity[l]+','+(p[l]+2*capacity[l]);counts.set(key,(counts.get(key)||0)+1);answer+=counts.get(capacity[r]+','+p[r])||0;}return answer;}

var countStableSubarrays = solve;
module.exports = solve;
