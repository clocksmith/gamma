const solve=a=>{const b=a.length,c=a[0].length;const d=Array(c).fill(Infinity);d[0]=0;for(let e=0;e<b;e++){for(let b=0;b<c;b++){d[b]=a[e][b]+Math.min(d[b],b?d[b-1]:Infinity);}}return d[c-1];};
