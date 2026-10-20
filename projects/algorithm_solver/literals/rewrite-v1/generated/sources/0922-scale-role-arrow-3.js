const solve=a=>{let r=1;for(let i=0;i<a.length;i+=2){if(a[i]%2!==0){while(r<a.length&&a[r]%2!==0){r+=2;}if(r>=a.length){throw'parity count mismatch';}const b=a[i];a[i]=a[r];a[r]=b;}}return a;};
