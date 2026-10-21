function solve(a){const r=[[]];for(const x of a){const a=r.length;for(let i=0;i<a;i+=1){r.push([...r[i],x]);}}return r;}
