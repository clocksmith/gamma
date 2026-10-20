function solve(a){let b=0;let c=0;for(const d of a){if(d==='U'){c+=1;}else if(d==='D'){c-=1;}else if(d==='L'){b-=1;}else if(d==='R'){b+=1;}}return b===0&&c===0;}
