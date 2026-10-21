function solve(a,b){const c=Array(b).fill(1n);for(let i=1;i<a;i++){for(let i=1;i<b;i++){c[i]+=c[i-1];}}const d=c[b-1];return d<=BigInt(Number.MAX_SAFE_INTEGER)?Number(d):d;}
