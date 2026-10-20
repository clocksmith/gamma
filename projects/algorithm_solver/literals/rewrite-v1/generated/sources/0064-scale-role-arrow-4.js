const solve=a=>{const b=a.length,c=a[0].length;const d=Array(c).fill(Infinity);d[0]=0;for(let i=0;i<b;i++){for(let j=0;j<c;j++){d[j]=a[i][j]+Math.min(d[j],j?d[j-1]:Infinity);}}return d[c-1];};
