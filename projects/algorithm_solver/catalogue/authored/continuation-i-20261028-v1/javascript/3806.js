function solve(nums,k,m){let answer=0;for(let bit=30;bit>=0;bit--){const mask=answer|(2**bit),costs=[];for(const x of nums){const missing=mask&~x;if(missing===0)costs.push(0);else{const b=31-Math.clz32(missing),half=2**b,unit=2*half,y=Math.floor(x/unit)*unit+half+(mask%half);costs.push(y-x);}}costs.sort((a,b)=>a-b);let total=0;for(let i=0;i<m;i++)total+=costs[i];if(total<=k)answer=mask;}return answer;}

var maximumAND = solve;
module.exports = solve;
