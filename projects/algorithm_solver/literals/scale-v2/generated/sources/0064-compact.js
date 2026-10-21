function solve(a){const b=a.length,c=a[0].length;const d=Array(c).fill(Infinity);d[0]=0;for(let e=0;e<b;e++){for(let f=0;f<c;f++){d[f]=a[e][f]+Math.min(d[f],f?d[f-1]:Infinity);}}return d[c-1];}
