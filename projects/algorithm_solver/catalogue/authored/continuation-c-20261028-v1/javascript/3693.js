function solve(n,costs){const recent=[0,Infinity,Infinity];for(let i=1;i<=n;i++){let best=Infinity;for(let jump=1;jump<=Math.min(3,i);jump++)best=Math.min(best,recent[(i-jump)%3]+jump*jump);recent[i%3]=costs[i-1]+best;}return recent[n%3];}

var climbStairs = solve;
module.exports = solve;
