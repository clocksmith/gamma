function solve(technique1,technique2,k){const gains=technique1.map((a,i)=>a-technique2[i]).sort((a,b)=>b-a);let answer=0;for(const x of technique2)answer+=x;for(let i=0;i<gains.length;i++)if(i<k||gains[i]>0)answer+=gains[i];return answer;}

var maxPoints = solve;
module.exports = solve;
