function solve(n,pos,k){const mod=1000000007n;k=Math.min(k,n-1-k);let numerator=1n,denominator=1n;for(let i=1;i<=k;i++){numerator=numerator*BigInt(n-i)%mod;denominator=denominator*BigInt(i)%mod;}function power(base,exp){let result=1n;while(exp){if(exp&1n)result=result*base%mod;base=base*base%mod;exp>>=1n;}return result;}return Number(2n*numerator*power(denominator,mod-2n)%mod);}

var countVisiblePeople = solve;
module.exports = solve;

