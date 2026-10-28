function solve(n){const prime=new Uint8Array(n+1);prime.fill(1);prime[0]=prime[1]=0;for(let p=2;p*p<=n;p++)if(prime[p])for(let x=p*p;x<=n;x+=p)prime[x]=0;let total=0,answer=0;for(let p=2;p<=n;p++)if(prime[p]){total+=p;if(total>n)break;if(prime[total])answer=total;}return answer;}

var largestPrime = solve;
module.exports = solve;
