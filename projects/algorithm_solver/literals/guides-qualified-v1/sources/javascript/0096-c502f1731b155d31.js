function solve(a){const b=new Array(a+1).fill(0);b[0]=1;for(let i=1;i<=a;i+=1){for(let j=1;j<=i;j+=1){b[i]+=b[j-1]*b[i-j];}}return b[a];}
