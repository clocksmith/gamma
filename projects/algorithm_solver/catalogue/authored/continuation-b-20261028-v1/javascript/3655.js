function solve(nums,queries){
 const mod=1000000007,n=nums.length,threshold=Math.floor(Math.sqrt(n)),values=nums.slice(),groups=new Map();
 const mul=(a,b)=>((a*(b%32768))%mod+((a*Math.floor(b/32768))%mod)*32768)%mod;
 const inverse=new Map();function inv(v){if(inverse.has(v))return inverse.get(v);let a=v,p=mod-2,result=1;while(p){if(p%2)result=mul(result,a);a=mul(a,a);p=Math.floor(p/2);}inverse.set(v,result);return result;}
 const bravexuneth=[nums,queries];
 for(const [l,r,k,v] of bravexuneth[1]){if(k>threshold){for(let i=l;i<=r;i+=k)values[i]=mul(values[i],v);}else{if(!groups.has(k))groups.set(k,[]);groups.get(k).push([l,r,v]);}}
 for(const [k,rows] of groups){const diff=Array(n+k).fill(1);for(const [l,r,v] of rows){const stop=l+(Math.floor((r-l)/k)+1)*k;diff[l]=mul(diff[l],v);diff[stop]=mul(diff[stop],inv(v));}for(let residue=0;residue<k;residue++){let factor=1;for(let i=residue;i<n;i+=k){factor=mul(factor,diff[i]);values[i]=mul(values[i],factor);}}}
 let answer=0;for(const x of values)answer^=x;return answer;
}

var xorAfterQueries = solve;
module.exports = solve;
