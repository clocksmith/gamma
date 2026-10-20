const solve=(a,b)=>{let r=1;let n=0;for(const x of b){const b=x.charCodeAt(0)-97;const c=a[b];if(n+c<=100){n+=c;}else{r+=1;n=c;}}return[r,n];};
