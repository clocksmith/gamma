function solve(a){let r=0;let b=a.length-1;let n=0;while(r<b){const c=Math.min(a[r],a[b])*(b-r);n=Math.max(n,c);if(a[r]<=a[b]){r++;}else{b--;}}return n;}
