function solve(n,l,r){
 const mod=1000000007,width=r-l+1,size=width-1;
 const mul=(a,b)=>((a*(b%32768))%mod+((a*Math.floor(b/32768))%mod)*32768)%mod;
 let matrix=Array.from({length:size},(_,i)=>Array.from({length:size},(_,j)=>Number(j+1>=width-(i+1)))),vector=Array(size).fill(1),exponent=n-1;
 function square(a){const out=Array.from({length:size},()=>Array(size).fill(0));for(let i=0;i<size;i++)for(let k=0;k<size;k++)if(a[i][k])for(let j=0;j<size;j++)out[i][j]=(out[i][j]+mul(a[i][k],a[k][j]))%mod;return out;}
 while(exponent){if(exponent%2){const next=Array(size).fill(0);for(let i=0;i<size;i++)for(let j=0;j<size;j++)next[i]=(next[i]+mul(matrix[i][j],vector[j]))%mod;vector=next;}exponent=Math.floor(exponent/2);if(exponent)matrix=square(matrix);}
 let answer=0;for(const v of vector)answer=(answer+2*v)%mod;return answer;
}

var zigZagArrays = solve;
module.exports = solve;
