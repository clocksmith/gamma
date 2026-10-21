function solve(a,b){const c=a.split('');for(let d=0;d<c.length;d+=2*b){let e=d;let f=d+b;if(f>c.length){f=c.length;}while(e+1<f){f-=1;const g=c[e];c[e]=c[f];c[f]=g;e+=1;}}return c.join('');}
