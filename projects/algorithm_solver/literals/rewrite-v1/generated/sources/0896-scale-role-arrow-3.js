const solve=a=>{let r=true;let n=true;for(let i=1;i<a.length;i+=1){if(a[i-1]>a[i]){r=false;}if(a[i-1]<a[i]){n=false;}}return r||n;};
