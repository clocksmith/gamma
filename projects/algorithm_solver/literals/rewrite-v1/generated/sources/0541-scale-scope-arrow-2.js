const solve=(a,b)=>{const c=a.split('');for(let a=0;a<c.length;a+=2*b){let d=a;let e=a+b;if(e>c.length){e=c.length;}while(d+1<e){e-=1;const a=c[d];c[d]=c[e];c[e]=a;d+=1;}}return c.join('');};
