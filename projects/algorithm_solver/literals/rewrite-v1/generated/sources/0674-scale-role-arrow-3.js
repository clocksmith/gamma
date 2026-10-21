const solve=a=>{let r=1;let n=1;for(let i=1;i<a.length;i+=1){if(a[i-1]<a[i]){r+=1;if(r>n){n=r;}}else{r=1;}}return n;};
