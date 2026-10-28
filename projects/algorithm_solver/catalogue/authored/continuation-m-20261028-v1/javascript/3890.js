function solve(n){const cubes=[];for(let x=1;x*x*x<=n;x++)cubes.push(x*x*x);const counts=new Map();for(let i=0;i<cubes.length;i++)for(let j=i;j<cubes.length;j++){const total=cubes[i]+cubes[j];if(total>n)break;counts.set(total,(counts.get(total)||0)+1);}const answer=[];for(const [value,count] of counts)if(count>=2)answer.push(value);return answer.sort((a,b)=>a-b);}

var findGoodIntegers = solve;
module.exports = solve;

