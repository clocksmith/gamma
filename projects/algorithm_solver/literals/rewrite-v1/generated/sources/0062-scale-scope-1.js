function solve(a,b){const c=Array(b).fill(1n);for(let d=1;d<a;d++){for(let a=1;a<b;a++){c[a]+=c[a-1];}}const d=c[b-1];return d<=BigInt(Number.MAX_SAFE_INTEGER)?Number(d):d;}
