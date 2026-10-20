function solve(a){let b=1;for(let c=0;c<a.length;c+=2){if(a[c]%2!==0){while(b<a.length&&a[b]%2!==0){b+=2;}if(b>=a.length){throw'parity count mismatch';}const d=a[c];a[c]=a[b];a[b]=d;}}return a;}
