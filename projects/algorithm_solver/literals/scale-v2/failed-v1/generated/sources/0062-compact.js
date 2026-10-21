function solve(a,b){const c=Array(b).fill(1n);for(let e=1;e<a;e++){for(let f=1;f<b;f++){c[f]+=c[f-1];}}const d=c[b-1];return d<=BigInt(Number.MAX_SAFE_INTEGER)?Number(d):d;}
