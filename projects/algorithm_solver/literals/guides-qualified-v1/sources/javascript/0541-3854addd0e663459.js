function solve(a,b){const c=a.split('');for(let i=0;i<c.length;i+=2*b){let a=i;let d=i+b;if(d>c.length){d=c.length;}while(a+1<d){d-=1;const b=c[a];c[a]=c[d];c[d]=b;a+=1;}}return c.join('');}
